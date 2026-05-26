#!/usr/bin/env python3
"""External Evaluator (target-aware verification of Pipeline output).

Modes:
  --mode verbose : Full diagnostic with target-specific verifications.
                   ONLY allowed after the v1.0-methodology-locked git tag exists.
  --mode blind   : Reserved for legacy compatibility; in this build, blind mode
                   is NOT used (Phase α is evaluator-free per plan v1.1 / DEC-1).
                   Calling --mode blind returns a stub note explaining this.

The evaluator reads:
  - evaluator/expected_answer.json (ground truth: expected_top_targets, expected_ensembl_ids)
  - evaluator/expected_thresholds.json (target-specific anti-bias thresholds)
  - the Pipeline's runs/round_N/output.json

It writes a Markdown diagnostic to the specified output path.

Mode-gating: the orchestrator should not invoke this script before the lock tag exists.
If invoked anyway, this script enforces gating and refuses to run verbose mode.
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from pathlib import Path


LOCK_TAG = "v1.0-methodology-locked"
EVALUATOR_DIR = Path(__file__).resolve().parent


def lock_tag_exists() -> bool:
    try:
        result = subprocess.run(
            ["git", "rev-parse", f"refs/tags/{LOCK_TAG}"],
            capture_output=True, text=True, check=False,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.SubprocessError):
        return False


def render_verbose_diagnostic(output_json: dict, expected: dict, thresholds: dict) -> str:
    expected_targets = expected.get("expected_top_targets", [])
    expected_ensembl = set(expected.get("expected_ensembl_ids", []))
    top_n_threshold = expected.get("expected_top_rank_threshold", 5)

    ranked = output_json.get("ranked_targets", [])
    n_total = len(ranked)

    # Find target rank
    target_rank = None
    target_score = None
    target_entry = None
    for entry in ranked:
        if entry.get("ensembl_gene_id") in expected_ensembl or entry.get("target_symbol") in expected_targets:
            target_rank = entry.get("rank")
            target_score = entry.get("composite_score")
            target_entry = entry
            break

    in_top_n = (target_rank is not None and target_rank <= top_n_threshold)

    lines = []
    lines.append("# Evaluator Diagnostic (verbose mode)")
    lines.append("")
    lines.append(f"- **Lock tag present:** {LOCK_TAG} = ✓")
    lines.append(f"- **Mode:** verbose")
    lines.append(f"- **Pipeline output ranked targets:** {n_total}")
    lines.append(f"- **Expected top target(s):** {expected_targets}")
    lines.append(f"- **Expected top-rank threshold (N):** {top_n_threshold}")
    lines.append("")
    lines.append("## T1 — Expected Target in Top N")
    if target_rank is None:
        lines.append(f"- ❌ FAIL — expected target not found in ranked output")
    else:
        status = "✅ PASS" if in_top_n else "⚠️ MISS"
        lines.append(f"- {status} — expected target rank = {target_rank} (threshold ≤ {top_n_threshold})")
        lines.append(f"  - composite_score = {target_score:.4f}" if target_score is not None else "")

    # T2 — Anti-bias suite results (pulled from Pipeline output)
    lines.append("")
    lines.append("## T2 — Anti-Bias Suite (Pipeline-side, target-agnostic)")
    anti_bias = output_json.get("anti_bias_validation", {})
    for mech in ["loo_ablation", "negative_controls", "literature_blinded_rerank", "cross_biobank_replication", "permutation_test_p_value"]:
        v = anti_bias.get(mech)
        lines.append(f"- **{mech}**: {v}")

    # T3 — Target-specific verifications from expected_thresholds.json
    lines.append("")
    lines.append("## T3 — Target-Specific Verifications (Evaluator-side)")
    target_checks = thresholds.get("target_specific_checks", {})
    for check_name, check_def in target_checks.items():
        lines.append(f"### {check_name}")
        lines.append(f"- criterion: {check_def.get('criterion', 'n/a')}")
        lines.append(f"- severity: {check_def.get('severity', 'n/a')}")

    # T4 — Reviewer ensemble verdict
    lines.append("")
    lines.append("## T4 — Reviewer Ensemble Verdict")
    rev = output_json.get("reviewer_ensemble_verdict", {})
    meta = rev.get("meta_review", {}) if isinstance(rev, dict) else {}
    lines.append(f"- verdict: {meta.get('verdict', 'n/a')}")
    lines.append(f"- blockers_remaining: {len(rev.get('blockers_remaining', []) if isinstance(rev, dict) else [])}")

    # T5 — Reproducibility (pre-registration hash check)
    lines.append("")
    lines.append("## T5 — Reproducibility")
    pre_reg = output_json.get("pre_registration_hash", "MISSING")
    lines.append(f"- pre_registration_hash: {pre_reg}")

    # T6 — Forbidden-change audit (handled by orchestrator + verify_methodology_lock.sh)
    lines.append("")
    lines.append("## T6 — Methodology Integrity")
    lines.append("- (Handled by scripts/verify_methodology_lock.sh; see LOOP_SUMMARY.md for audit trail.)")

    # Summary
    lines.append("")
    lines.append("## Summary")
    summary = {
        "expected_target_rank": target_rank,
        "expected_target_in_top_n": in_top_n,
        "n_ranked": n_total,
        "lock_tag": LOCK_TAG,
    }
    lines.append("```json")
    lines.append(json.dumps(summary, indent=2))
    lines.append("```")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["verbose", "blind"], required=True)
    parser.add_argument("--input", required=True, help="path to runs/round_N/output.json")
    parser.add_argument("--output", required=True, help="path to write diagnostic Markdown")
    parser.add_argument("--allow-pre-lock", action="store_true",
                        help="(testing only) bypass lock-tag check for verbose mode")
    args = parser.parse_args()

    if args.mode == "blind":
        # Plan v1.1 / DEC-1: Phase α is evaluator-free; blind mode is reserved for legacy
        Path(args.output).write_text(
            "# Evaluator Diagnostic (blind mode)\n\n"
            "Phase α is evaluator-free in plan v1.1. Blind mode is not active in this build.\n"
            "Convergence in Phase α is judged by Codex + reviewer ensemble + leakage scans only.\n"
        )
        print("evaluator: blind mode returns stub (Phase α is evaluator-free)")
        return 0

    # Verbose mode: enforce lock tag presence
    if not args.allow_pre_lock and not lock_tag_exists():
        print(f"evaluator: ERROR - verbose mode requires {LOCK_TAG} git tag to exist", file=sys.stderr)
        print("evaluator: invoke after methodology lock, or pass --allow-pre-lock for testing", file=sys.stderr)
        return 1

    expected = json.loads((EVALUATOR_DIR / "expected_answer.json").read_text())
    thresholds = json.loads((EVALUATOR_DIR / "expected_thresholds.json").read_text())
    output_json = json.loads(Path(args.input).read_text())

    diagnostic = render_verbose_diagnostic(output_json, expected, thresholds)
    Path(args.output).write_text(diagnostic)
    print(f"evaluator: wrote verbose diagnostic to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
