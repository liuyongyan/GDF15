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
    n_total = output_json.get("ranked_targets_full_count", len(ranked))

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
    lines.append(f"- **Pipeline output ranked candidates (emitted):** {len(ranked)}")
    lines.append(f"- **Pipeline output ranked candidates (total in universe):** {n_total}")
    lines.append(f"- **Expected top target(s):** {expected_targets}")
    lines.append(f"- **Expected top-rank threshold (N):** {top_n_threshold}")
    lines.append("")

    # T1 — Expected Target in Top N (computed)
    lines.append("## T1 — Expected Target in Top N (computed)")
    if target_rank is None:
        lines.append(f"- ❌ FAIL — expected target not found in ranked output")
    else:
        status = "✅ PASS" if in_top_n else "⚠️ MISS"
        lines.append(f"- {status} — expected target rank = {target_rank} of {n_total} (threshold ≤ {top_n_threshold})")
        if target_score is not None:
            lines.append(f"  - composite_score = {target_score:.4f}")

    # Per-dimension target contributions (computed)
    lines.append("")
    lines.append("## Per-Dimension Target Contributions (computed)")
    if target_entry and target_entry.get("per_dimension_scores"):
        weights = output_json.get("weights_used", {})
        per_dim = target_entry["per_dimension_scores"]
        lines.append("| Dimension | Score (z) | Weight | Weighted Contribution | Missingness |")
        lines.append("|---|---|---|---|---|")
        total_weighted = 0.0
        for dim, sc in sorted(per_dim.items()):
            w = weights.get(dim, 0.0)
            contribution = w * sc
            total_weighted += contribution
            miss_flag = (target_entry.get("per_dimension_missingness") or {}).get(dim, False)
            lines.append(f"| {dim} | {sc:+.4f} | {w:.4f} | {contribution:+.4f} | {miss_flag} |")
        lines.append(f"| **Sum of weighted contributions** | | | **{total_weighted:+.4f}** | |")
    else:
        lines.append("- (target entry not found in emitted top-N; cannot compute contributions)")

    # T2 — Anti-bias suite results from Pipeline (target-agnostic)
    lines.append("")
    lines.append("## T2 — Pipeline-Side Anti-Bias Suite Results (target-agnostic)")
    anti_bias = output_json.get("anti_bias_validation", {})
    lines.append("| Mechanism | Result |")
    lines.append("|---|---|")
    for mech in ["loo_ablation", "negative_controls", "literature_blinded_rerank", "cross_biobank_replication", "permutation_test_p_value"]:
        v = anti_bias.get(mech)
        lines.append(f"| {mech} | `{v}` |")
    # If the pipeline propagated validation_summary, surface its statuses
    val_summary = anti_bias.get("validation_summary")
    if val_summary:
        lines.append("")
        lines.append("### Per-mechanism threshold status")
        for s in val_summary.get("statuses", []):
            lines.append(f"- **{s.get('mechanism')}**: {s.get('status')} (severity={s.get('severity')})"
                          + (f" — actual={s.get('actual')}, threshold={s.get('threshold')}" if "actual" in s else ""))
        lines.append(f"- Hard failures: {val_summary.get('failed_hard_count', 0)}; "
                      f"Soft failures: {val_summary.get('failed_soft_count', 0)}")

    # T3 — Target-specific verifications (computed)
    lines.append("")
    lines.append("## T3 — Target-Specific Anti-Bias Verifications (computed)")
    target_checks = thresholds.get("target_specific_checks", {})

    # 3a: expected_target_in_top_n
    cb = target_checks.get("expected_target_in_top_n", {})
    if cb:
        lines.append(f"### expected_target_in_top_n")
        lines.append(f"- criterion: {cb.get('criterion', 'target in top ' + str(cb.get('n', top_n_threshold)))}")
        lines.append(f"- severity: {cb.get('severity')}")
        lines.append(f"- result: **{'PASS' if in_top_n else 'FAIL'}** — rank={target_rank}, threshold≤{cb.get('n', top_n_threshold)}")

    # 3b: negative_controls_bottom_half (computed from validation_summary if available)
    cb = target_checks.get("negative_controls_bottom_half", {})
    if cb:
        lines.append(f"### negative_controls_bottom_half")
        nc_actual = None
        nc_status = "UNKNOWN"
        if val_summary:
            for s in val_summary.get("statuses", []):
                if s.get("mechanism") == "negative_controls":
                    nc_actual = s.get("actual")
                    nc_status = s.get("status")
                    break
        lines.append(f"- criterion: {cb.get('criterion')}")
        lines.append(f"- severity: {cb.get('severity')}")
        lines.append(f"- result: **{nc_status}** — mean_percentile={nc_actual}")

    # 3c: loo_ablation_target_stability — compute per-dim target rank under each LOO
    cb = target_checks.get("loo_ablation_target_stability", {})
    if cb:
        loo = anti_bias.get("loo_ablation", {})
        lines.append(f"### loo_ablation_target_stability")
        lines.append(f"- criterion: {cb.get('criterion')}")
        lines.append(f"- severity: {cb.get('severity')}")
        # Read the per_dim_results from the raw _results_loo.json (loo in output is summarized)
        try:
            loo_raw_path = Path(__file__).resolve().parent.parent / "pipeline" / "anti_bias" / "_results_loo.json"
            if loo_raw_path.exists():
                loo_raw = json.loads(loo_raw_path.read_text())
                per_dim = loo_raw.get("per_dim_results", {})
                lines.append(f"- per-dim target ranks under LOO:")
                lines.append("  | Removed Dim | Target rank | Δ from full |")
                lines.append("  |---|---|---|")
                all_pass = True
                for dim, res in per_dim.items():
                    for change in res.get("original_top5_rank_changes", []):
                        if expected_ensembl and change.get("ensembl") in expected_ensembl:
                            new_rank = change.get("new_rank")
                            delta = change.get("delta")
                            ok = new_rank is not None and new_rank <= top_n_threshold
                            if not ok:
                                all_pass = False
                            marker = "✓" if ok else "✗"
                            lines.append(f"  | {dim} | {new_rank} {marker} | {delta:+d} |")
                lines.append(f"- result: **{'PASS' if all_pass else 'FAIL'}** — target remains in top {top_n_threshold} under every LOO")
            else:
                lines.append("- result: UNKNOWN — _results_loo.json not found")
        except Exception as e:
            lines.append(f"- result: UNKNOWN — error reading LOO results: {e}")

    # 3d: permutation_test_top_target_significance
    cb = target_checks.get("permutation_test_top_target_significance", {})
    if cb:
        pv = anti_bias.get("permutation_test_p_value")
        lines.append(f"### permutation_test_top_target_significance")
        lines.append(f"- criterion: {cb.get('criterion')}")
        lines.append(f"- severity: {cb.get('severity')}")
        lines.append(f"- result: empirical p-value = {pv}")

    # 3e: literature_blinded_target_top_quartile — compute from _results_lit_blind.json
    cb = target_checks.get("literature_blinded_target_top_quartile", {})
    if cb:
        lines.append(f"### literature_blinded_target_top_quartile")
        lines.append(f"- criterion: {cb.get('criterion')}")
        lines.append(f"- severity: {cb.get('severity')}")
        try:
            lit_raw_path = Path(__file__).resolve().parent.parent / "pipeline" / "anti_bias" / "_results_lit_blind.json"
            if lit_raw_path.exists():
                lit_raw = json.loads(lit_raw_path.read_text())
                blinded_top25 = lit_raw.get("blinded_top25_ranking", [])
                target_blinded_rank = None
                for e in blinded_top25:
                    if e.get("ensembl_gene_id") in expected_ensembl:
                        target_blinded_rank = e.get("rank")
                        break
                # Approximate: top-25 percentile = (rank / total_universe) * 100
                if target_blinded_rank is None:
                    lines.append(f"- result: UNKNOWN — target not in blinded_top25 (rank may exceed 25)")
                else:
                    pct = (target_blinded_rank / n_total) * 100.0 if n_total else None
                    in_top_quartile = pct is not None and pct <= 25.0
                    lines.append(f"- result: **{'PASS' if in_top_quartile else 'FAIL'}** — blinded rank = {target_blinded_rank}, percentile = {pct:.2f}%, threshold ≤ 25%")
            else:
                lines.append("- result: UNKNOWN — _results_lit_blind.json not found")
        except Exception as e:
            lines.append(f"- result: UNKNOWN — error: {e}")

    # 3f: platform_post_hoc_compatibility — READ THE TSV, not just point at it
    cb = target_checks.get("platform_post_hoc_compatibility", {})
    if cb and target_entry:
        lines.append(f"### platform_post_hoc_compatibility")
        lines.append(f"- criterion: {cb.get('criterion')}")
        lines.append(f"- severity: {cb.get('severity')}")
        # Read the platform_compatibility TSV (most recent round)
        import csv as _csv
        platform_tsv = None
        runs_dir = Path(__file__).resolve().parent.parent / "runs"
        if runs_dir.exists():
            for d in sorted(runs_dir.iterdir(), reverse=True):
                tsv = d / "platform_compatibility_top25.tsv"
                if tsv.exists():
                    platform_tsv = tsv
                    break
        target_platform_result = None
        if platform_tsv:
            with platform_tsv.open() as f:
                reader = _csv.DictReader(f, delimiter="\t")
                for row in reader:
                    if row.get("ensembl_gene_id") in expected_ensembl:
                        target_platform_result = row
                        break
        if target_platform_result:
            lines.append(f"- result: **{target_platform_result.get('platform_compatible_overall', 'UNKNOWN')}**")
            lines.append(f"  - secreted: {target_platform_result.get('is_secreted')} → {target_platform_result.get('passes_secretion')}")
            lines.append(f"  - ORF size: {target_platform_result.get('orf_length_bp')} bp → {target_platform_result.get('passes_orf_size')}")
            lines.append(f"  - signal peptide: {target_platform_result.get('signal_peptide')} → {target_platform_result.get('passes_signal')}")
            lines.append(f"- source: {platform_tsv.relative_to(Path(__file__).resolve().parent.parent)}")
        else:
            lines.append("- result: UNKNOWN — platform_compatibility_top25.tsv not found or target not in top-25")
            lines.append(f"- (D5 secretion/modulatability score: {(target_entry.get('per_dimension_scores') or {}).get('D5_secretion_and_modulatability')})")
            lines.append(f"- (D8 platform deliverability score, excluded from composite: {(target_entry.get('per_dimension_scores') or {}).get('D8_platform_deliverability')})")

    # T4 — Reviewer ensemble verdict
    lines.append("")
    lines.append("## T4 — Reviewer Ensemble Verdict")
    rev = output_json.get("reviewer_ensemble_verdict", {})
    meta = rev.get("meta_review", {}) if isinstance(rev, dict) else {}
    lines.append(f"- mode: {rev.get('mode', 'n/a') if isinstance(rev, dict) else 'n/a'}")
    lines.append(f"- status: {rev.get('status', 'n/a') if isinstance(rev, dict) else 'n/a'}")
    lines.append(f"- verdict: {meta.get('verdict', 'n/a')}")
    blockers = rev.get("blockers_remaining", []) if isinstance(rev, dict) else []
    lines.append(f"- blockers_remaining: {len(blockers)} {(' — ' + ', '.join(str(b) for b in blockers)) if blockers else ''}")
    if isinstance(rev, dict) and rev.get("reason"):
        lines.append(f"- reason: {rev['reason']}")

    # T5 — Reproducibility
    lines.append("")
    lines.append("## T5 — Reproducibility")
    pre_reg = output_json.get("pre_registration_hash", "MISSING")
    lines.append(f"- pre_registration_hash: `{pre_reg}`")
    lines.append(f"- expected: commit SHA bearing tag `{LOCK_TAG}` (not annotated-tag SHA)")
    lines.append(f"- reproduce: `bash pipeline/run_pipeline.sh sample_input.json out.json 0`")

    # T6 — Methodology integrity
    lines.append("")
    lines.append("## T6 — Methodology Integrity")
    lines.append("- Audit: run `bash scripts/verify_methodology_lock.sh` to confirm no forbidden-mutability artifact has changed since lock.")
    lines.append("- Source-code leakage scan: run `bash scripts/scan_target_leakage.sh pipeline` to confirm zero hits.")

    # Summary block
    lines.append("")
    lines.append("## Summary")
    summary = {
        "expected_target_rank": target_rank,
        "expected_target_in_top_n": in_top_n,
        "n_ranked_total": n_total,
        "lock_tag": LOCK_TAG,
        "pre_registration_hash": pre_reg,
        "reviewer_status": (rev.get("status") if isinstance(rev, dict) else None) or (rev.get("mode") if isinstance(rev, dict) else None),
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
        # AC-1.1 contract: blind mode returns categorical JSON only.
        # Note: per plan v1.1, Phase α is evaluator-free; the Loop should not invoke this.
        # If invoked anyway (e.g., during integration testing), we return the AC-1.1 JSON
        # contract — purely categorical pass/fail with NO target-specific information.
        expected = json.loads((EVALUATOR_DIR / "expected_answer.json").read_text())
        thresholds = json.loads((EVALUATOR_DIR / "expected_thresholds.json").read_text())

        output_doc = None
        if Path(args.input).exists():
            try:
                output_doc = json.loads(Path(args.input).read_text())
            except json.JSONDecodeError:
                output_doc = None

        # Compute booleans WITHOUT exposing any rank/score detail
        t1 = False
        t2 = False
        t3 = False
        t4 = False
        t5 = False
        t6 = False
        if output_doc and isinstance(output_doc.get("ranked_targets"), list):
            expected_ensembl = set(expected.get("expected_ensembl_ids", []))
            top_n = expected.get("expected_top_rank_threshold", 5)
            for entry in output_doc["ranked_targets"][:top_n]:
                if entry.get("ensembl_gene_id") in expected_ensembl:
                    t1 = True
                    break
            anti_bias = output_doc.get("anti_bias_validation", {})
            t2 = bool(anti_bias) and all(
                v is not None for v in anti_bias.values()
            )
            t3 = anti_bias.get("permutation_test_p_value") is not None
            rev = output_doc.get("reviewer_ensemble_verdict", {})
            if isinstance(rev, dict):
                # Tightened T4: deferred-reviewer-status CANNOT count as PASS
                rev_status = rev.get("status", "")
                rev_mode = rev.get("mode", "")
                is_deferred = (rev_status == "REVIEWER_DEFERRED") or rev_mode.startswith("REVIEWER_DEFERRED") or "MOCK_STUB" in rev_mode
                t4 = (not is_deferred) and (rev.get("status") != "BLOCKED") and (len(rev.get("blockers_remaining", [])) == 0)
            t5 = bool(output_doc.get("pre_registration_hash"))
            t6 = output_doc.get("pre_registration_hash", "").endswith("_pre_lock") is False

        # AC-1.1 strict contract: exactly six T*_pass boolean keys, no metadata
        blind_result = {
            "T1_pass": t1,
            "T2_pass": t2,
            "T3_pass": t3,
            "T4_pass": t4,
            "T5_pass": t5,
            "T6_pass": t6,
        }
        Path(args.output).write_text(json.dumps(blind_result, indent=2, sort_keys=True))
        print("evaluator: blind mode wrote categorical JSON (AC-1.1 strict 6-key contract)")
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
