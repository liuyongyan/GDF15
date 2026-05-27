#!/usr/bin/env python3
"""Build an anonymized reviewer dossier directly from the CURRENT run.

Per Round 9: the dossier must come from the same-run scoring + anti-bias artifacts,
NOT from a prior output.json picked by mtime. This guarantees reviewers critique the
ranking the same run is about to assemble.

Inputs (all same-run):
- pipeline/universe/candidate_universe.tsv
- pipeline/scoring/_scores_*.tsv
- pipeline/scoring/weights.json
- pipeline/anti_bias/_validation_summary.json (optional; produced by anti_bias suite)

The dossier ranks candidates by composite z = sum(weight_d * score_d) over the 7 dims
that contribute to the composite (excluded dims read from weights.json).
"""
from __future__ import annotations
import argparse
import csv
import json
import sys
from pathlib import Path


PIPELINE_ROOT = Path(__file__).resolve().parent.parent


def _load_universe() -> list[dict]:
    rows = []
    with (PIPELINE_ROOT / "universe" / "candidate_universe.tsv").open() as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            rows.append(r)
    return rows


def _load_score_tsv(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    with path.open() as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            eg = r["ensembl_gene_id"]
            score_col = next((k for k in r if k.startswith("score_")), None)
            try:
                score = float(r[score_col])
            except (ValueError, KeyError, TypeError):
                score = 0.0
            out[eg] = {"score": score, "dim_id": score_col[len("score_"):]}
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", type=int, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    scoring_dir = PIPELINE_ROOT / "scoring"
    weights_doc = json.loads((scoring_dir / "weights.json").read_text())
    weights = weights_doc["weights"]
    excluded = set(weights_doc.get("excluded_from_composite", []))

    universe = _load_universe()
    per_dim: dict[str, dict[str, dict]] = {}
    for p in sorted(scoring_dir.glob("_scores_*.tsv")):
        scores = _load_score_tsv(p)
        if not scores:
            continue
        dim_id = next(iter(scores.values()))["dim_id"]
        per_dim[dim_id] = scores

    enriched: list[dict] = []
    for u in universe:
        eg = u["ensembl_gene_id"]
        per_dim_scores = {d: per_dim.get(d, {}).get(eg, {"score": 0.0})["score"] for d in per_dim}
        composite = sum(weights.get(d, 0.0) * v for d, v in per_dim_scores.items() if d not in excluded)
        enriched.append({
            "ensembl_gene_id": eg,
            "composite": composite,
            "per_dim": per_dim_scores,
        })
    enriched.sort(key=lambda r: -r["composite"])
    for rank, e in enumerate(enriched[:25], start=1):
        e["rank"] = rank

    anti_bias_summary = {}
    val_path = PIPELINE_ROOT / "anti_bias" / "_validation_summary.json"
    if val_path.exists():
        try:
            anti_bias_summary = json.loads(val_path.read_text())
        except json.JSONDecodeError:
            anti_bias_summary = {}

    lines: list[str] = []
    lines.append(f"# Anonymized Reviewer Dossier — Round {args.round} (same-run)")
    lines.append("")
    lines.append("## Provenance")
    lines.append(f"- Built from current-run artifacts (no prior output.json reference).")
    lines.append(f"- Universe size: {len(universe)} candidates")
    lines.append(f"- Dimensions contributing to composite: {sorted(set(per_dim.keys()) - excluded)}")
    lines.append(f"- Dimensions excluded from composite: {sorted(excluded)}")
    lines.append("")
    lines.append("## Anonymized top-25 candidates (this run)")
    lines.append("(Specific gene symbols intentionally withheld per pre-publication confidentiality.)")
    lines.append("")
    lines.append("| Candidate ID | Composite z | D1 genetic | D2 clinical | D3 assoc | D4 lit | D5 secret | D6 mech | D7 safety |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for e in enriched[:25]:
        sc = e["per_dim"]
        cid = f"candidate_{e['rank']:03d}"
        lines.append(
            f"| {cid} | {e['composite']:+.3f} | "
            f"{sc.get('D1_genetic_causal', 0):+.2f} | "
            f"{sc.get('D2_clinical_signal', 0):+.2f} | "
            f"{sc.get('D3_target_association_breadth', 0):+.2f} | "
            f"{sc.get('D4_literature_evidence', 0):+.2f} | "
            f"{sc.get('D5_secretion_and_modulatability', 0):+.2f} | "
            f"{sc.get('D6_mechanism_differentiation', 0):+.2f} | "
            f"{sc.get('D7_safety_proxy', 0):+.2f} |"
        )

    lines.append("")
    lines.append("## Anti-bias mechanism summary (this run)")
    if anti_bias_summary:
        for s in anti_bias_summary.get("statuses", []):
            actual = s.get('actual', 'n/a')
            thr = s.get('threshold', 'n/a')
            lines.append(f"- {s.get('mechanism')}: {s.get('status')} (severity={s.get('severity')}, actual={actual}, threshold={thr})")
        lines.append(f"- Hard failures: {anti_bias_summary.get('failed_hard_count', 0)}; "
                     f"Soft failures: {anti_bias_summary.get('failed_soft_count', 0)}")
    else:
        lines.append("- (_validation_summary.json not present; anti-bias suite not run yet)")

    lines.append("")
    lines.append("## Methodology summary")
    lines.append("- 8 scoring dimensions; 7 contribute to composite (equal weights of 1/7); 1 (platform_deliverability) excluded.")
    lines.append("- Anti-bias suite: LOO ablation, negative controls, literature-blinded re-rank with uniform NER redaction, cross-biobank MR (OPTIONAL_SKIPPED for bootstrap), permutation test.")
    lines.append("- Methodology pinned via git tag v1.0-methodology-locked; LOCKED_ARTIFACTS.json SHA256 manifest.")
    lines.append("")
    lines.append("Reviewers MUST return JSON in their output that includes `blockers_count` (integer) and `critiques` (array). Per AC-5, reviewer prose must NOT reference specific gene symbols.")

    Path(args.out).write_text("\n".join(lines) + "\n")
    print(f"build_reviewer_dossier: wrote {args.out} (same-run, {min(25, len(enriched))} candidates summarized)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
