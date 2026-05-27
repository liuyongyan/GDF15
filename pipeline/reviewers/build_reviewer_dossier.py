#!/usr/bin/env python3
"""Build an anonymized reviewer dossier from the most recent assembled Pipeline output.

For AC-5, reviewers must see real anonymized candidate ranking + anti-bias status +
methodology summary — not a one-line stub.

Output format: plain text suitable for passing to each persona's prompt.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path


PIPELINE_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", type=int, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    # Find the most recent prior output.json
    runs_dir = PIPELINE_ROOT.parent / "runs"
    candidates = []
    if runs_dir.exists():
        for d in sorted(runs_dir.iterdir()):
            if d.name.startswith("round_") and (d / "output.json").exists():
                candidates.append(d)
    if not candidates:
        # No prior output; emit minimal context
        Path(args.out).write_text(
            f"Round {args.round}: no prior assembled Pipeline output available; "
            f"reviewer dossier minimal. Please critique the pipeline methodology in the "
            f"absence of a candidate ranking.\n"
        )
        return 0

    # Use the most recent output
    src = candidates[-1] / "output.json"
    doc = json.loads(src.read_text())
    ranked = doc.get("ranked_targets", [])[:25]
    n_total = doc.get("ranked_targets_full_count", len(ranked))
    anti_bias = doc.get("anti_bias_validation", {})
    val_summary = anti_bias.get("validation_summary", {})

    lines: list[str] = []
    lines.append(f"# Anonymized Reviewer Dossier — Round {args.round}")
    lines.append(f"(Source: {src.relative_to(PIPELINE_ROOT.parent)})")
    lines.append("")
    lines.append(f"## Pipeline output summary")
    lines.append(f"- Total candidates ranked: {n_total}")
    lines.append(f"- Methodology lock SHA: {doc.get('pre_registration_hash', 'UNKNOWN')}")
    lines.append("")
    lines.append("## Anonymized top-25 candidates")
    lines.append("(Specific gene symbols redacted per pre-publication confidentiality. Reviewer should evaluate using candidate IDs.)")
    lines.append("")
    lines.append("| Candidate ID | Composite z | D1 genetic | D2 clinical | D3 assoc | D4 lit | D5 secret | D6 mech | D7 safety |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for entry in ranked:
        sc = entry.get("per_dimension_scores", {}) or {}
        cid = f"candidate_{entry.get('rank', 0):03d}"
        lines.append(
            f"| {cid} | {entry.get('composite_score', 0):+.3f} | "
            f"{sc.get('D1_genetic_causal', 0):+.2f} | "
            f"{sc.get('D2_clinical_signal', 0):+.2f} | "
            f"{sc.get('D3_target_association_breadth', 0):+.2f} | "
            f"{sc.get('D4_literature_evidence', 0):+.2f} | "
            f"{sc.get('D5_secretion_and_modulatability', 0):+.2f} | "
            f"{sc.get('D6_mechanism_differentiation', 0):+.2f} | "
            f"{sc.get('D7_safety_proxy', 0):+.2f} |"
        )

    lines.append("")
    lines.append("## Anti-bias mechanism summary (Pipeline-side, target-agnostic)")
    if val_summary:
        for s in val_summary.get("statuses", []):
            lines.append(f"- {s.get('mechanism')}: {s.get('status')} (severity={s.get('severity')})"
                          + (f", actual={s.get('actual')}, threshold={s.get('threshold')}" if "actual" in s else ""))
        lines.append(f"- Hard failures: {val_summary.get('failed_hard_count', 0)}; "
                      f"Soft failures: {val_summary.get('failed_soft_count', 0)}")
    else:
        lines.append("- (validation_summary not present in source)")

    lines.append("")
    lines.append("## Methodology summary")
    lines.append("- 8 scoring dimensions; 7 contribute to composite (equal weights of 1/7); 1 (platform_deliverability) excluded.")
    lines.append("- Anti-bias suite: LOO ablation (Spearman ρ), negative controls (CETP, CB1R, HTR2C, DGAT1 percentiles), literature-blinded re-rank with uniform NER redaction, cross-biobank MR (OPTIONAL_SKIPPED for bootstrap), permutation test.")
    lines.append("- Methodology pinned via git tag v1.0-methodology-locked; LOCKED_ARTIFACTS.json SHA256 manifest with 51 artifacts.")
    lines.append("- Pre-registration commit SHA: " + doc.get('pre_registration_hash', 'UNKNOWN'))
    lines.append("")
    lines.append("Reviewers MUST return JSON in their output that includes `blockers_count` (integer) and `critiques` (array). Per AC-5, reviewer prose must NOT reference specific gene symbols.")

    Path(args.out).write_text("\n".join(lines) + "\n")
    print(f"build_reviewer_dossier: wrote {args.out} ({len(ranked)} candidates summarized)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
