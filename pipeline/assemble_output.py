#!/usr/bin/env python3
"""Assemble the final Pipeline output JSON conforming to AC-2 IO contract.

Reads:
  - pipeline/universe/candidate_universe.tsv
  - pipeline/scoring/_scores_D*.tsv (all dimensions)
  - pipeline/scoring/weights.json
  - pipeline/anti_bias/_results_*.json
  - runs/round_N/reviewer_ensemble_verdict.json
  - git HEAD or methodology-lock tag SHA
Writes:
  - <output_json> matching draft §3.1 output schema
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from pathlib import Path


PIPELINE_ROOT = Path(__file__).resolve().parent


def load_universe() -> list[dict]:
    import csv
    rows = []
    with (PIPELINE_ROOT / "universe" / "candidate_universe.tsv").open() as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            rows.append(r)
    return rows


def load_score_tsv(path: Path) -> dict[str, dict]:
    import csv
    out: dict[str, dict] = {}
    with path.open() as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            eg = r["ensembl_gene_id"]
            score_col = next((k for k in r if k.startswith("score_")), None)
            miss_col = next((k for k in r if k.startswith("missingness_")), None)
            try:
                score = float(r[score_col])
            except (ValueError, KeyError, TypeError):
                score = 0.0
            try:
                miss = bool(int(r[miss_col]))
            except (ValueError, KeyError, TypeError):
                miss = False
            out[eg] = {"score": score, "missing": miss, "dim_id": score_col[len("score_"):]}
    return out


def get_pre_registration_hash() -> str:
    # Use the COMMIT SHA bearing the lock tag (^{} dereferences annotated tags).
    # If no lock tag exists, fall back to HEAD marked _pre_lock.
    try:
        r = subprocess.run(
            ["git", "rev-parse", "refs/tags/v1.0-methodology-locked^{}"],
            capture_output=True, text=True, check=False, cwd=PIPELINE_ROOT.parent,
        )
        if r.returncode == 0:
            return r.stdout.strip()
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False, cwd=PIPELINE_ROOT.parent,
        )
        if r.returncode == 0:
            return r.stdout.strip() + "_pre_lock"
    except (FileNotFoundError, subprocess.SubprocessError):
        pass
    return "UNKNOWN"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviewer-verdict", required=True, help="path to reviewer_ensemble_verdict.json")
    parser.add_argument("--output", required=True, help="path to write pipeline output JSON")
    parser.add_argument("--round", type=int, default=0)
    args = parser.parse_args()

    universe = load_universe()

    # Load all per-dim scores
    scoring_dir = PIPELINE_ROOT / "scoring"
    weights = json.loads((scoring_dir / "weights.json").read_text())["weights"]
    excluded = set(json.loads((scoring_dir / "weights.json").read_text()).get("excluded_from_composite", []))

    all_score_files = sorted(scoring_dir.glob("_scores_*.tsv"))
    per_dim: dict[str, dict[str, dict]] = {}  # {dim_id: {ensembl: {score, missing}}}
    for p in all_score_files:
        scores = load_score_tsv(p)
        if not scores:
            continue
        dim_id = next(iter(scores.values()))["dim_id"]
        per_dim[dim_id] = scores

    # Compose ranked output
    enriched: list[dict] = []
    for u in universe:
        eg = u["ensembl_gene_id"]
        sym = u.get("gene_symbol", "")
        per_dim_scores: dict[str, float] = {}
        per_dim_missing: dict[str, bool] = {}
        composite = 0.0
        for dim_id, scores in per_dim.items():
            entry = scores.get(eg, {"score": 0.0, "missing": True})
            per_dim_scores[dim_id] = entry["score"]
            per_dim_missing[dim_id] = entry["missing"]
            if dim_id in weights:
                composite += weights[dim_id] * entry["score"]
        enriched.append({
            "ensembl_gene_id": eg,
            "target_symbol": sym,
            "composite_score": composite,
            "per_dimension_scores": per_dim_scores,
            "per_dimension_missingness": per_dim_missing,
            "predicted_phenotype_profile": {
                "fat_mass_reduction": "high" if per_dim_scores.get("D3_target_association_breadth", 0) > 0.5 else "moderate",
                "glycemic_control": "high" if per_dim_scores.get("D2_clinical_signal", 0) > 0.5 else "moderate",
                "hepatic_steatosis_reduction": "see_dim_breakdown",
                "lean_mass_preservation": "see_dim_breakdown",
                "durability": "depends_on_modality",
            },
            "recommended_delivery_modality": "TBD_post_hoc_platform_check",
            "rationale_summary": (
                f"composite={composite:.3f}; "
                f"strong dims: {[d for d, v in per_dim_scores.items() if v > 1.0]}"
            ),
        })

    enriched.sort(key=lambda r: -r["composite_score"])
    for rank, e in enumerate(enriched, start=1):
        e["rank"] = rank

    # Anti-bias rollup
    anti_bias_dir = PIPELINE_ROOT / "anti_bias"
    anti_bias = {}
    for key, fn in [
        ("loo_ablation", "_results_loo.json"),
        ("negative_controls", "_results_nc.json"),
        ("literature_blinded_rerank", "_results_lit_blind.json"),
        ("cross_biobank_replication", "_results_mr.json"),
        ("permutation_test_p_value", "_results_perm.json"),
    ]:
        p = anti_bias_dir / fn
        if p.exists():
            doc = json.loads(p.read_text())
            if key == "permutation_test_p_value":
                anti_bias[key] = doc.get("empirical_p_value")
            elif key == "cross_biobank_replication":
                anti_bias[key] = {"status": doc.get("status"), "reason": doc.get("reason")}
            elif key == "loo_ablation":
                anti_bias[key] = {
                    "aggregate_mean_rank_change": doc.get("aggregate_mean_rank_change"),
                    "aggregate_mean_spearman_rho": doc.get("aggregate_mean_spearman_rho"),
                }
            elif key == "negative_controls":
                anti_bias[key] = {
                    "mean_percentile": doc.get("mean_percentile_of_controls"),
                    "details": doc.get("controls"),
                }
            elif key == "literature_blinded_rerank":
                anti_bias[key] = {
                    "redaction_method": doc.get("redaction_method"),
                    "redacted_term_count": doc.get("redacted_term_count"),
                    "blinded_top25_ranking": doc.get("blinded_top25_ranking"),
                    "top5_overlap_count": doc.get("top5_overlap_count"),
                }
        else:
            anti_bias[key] = None

    # Propagate anti-bias validation_summary (PASS/FAIL per mechanism)
    val_summary_path = anti_bias_dir / "_validation_summary.json"
    if val_summary_path.exists():
        try:
            anti_bias["validation_summary"] = json.loads(val_summary_path.read_text())
        except json.JSONDecodeError:
            pass

    # Provide same-run artifact paths so the evaluator reads from these, not scratch defaults
    anti_bias_artifact_paths = {
        "loo": str((anti_bias_dir / "_results_loo.json").resolve()),
        "lit_blind": str((anti_bias_dir / "_results_lit_blind.json").resolve()),
        "nc": str((anti_bias_dir / "_results_nc.json").resolve()),
        "mr": str((anti_bias_dir / "_results_mr.json").resolve()),
        "perm": str((anti_bias_dir / "_results_perm.json").resolve()),
    }

    reviewer_verdict = json.loads(Path(args.reviewer_verdict).read_text())

    output = {
        "schema_version": "1.0",
        "round": args.round,
        "ranked_targets": enriched[:50],
        "ranked_targets_full_count": len(enriched),
        "anti_bias_validation": anti_bias,
        "anti_bias_artifact_paths": anti_bias_artifact_paths,
        "reviewer_ensemble_verdict": reviewer_verdict,
        "pre_registration_hash": get_pre_registration_hash(),
        "reproducibility": "./pipeline/run_pipeline.sh sample_input.json sample_output.json",
        "weights_used": weights,
        "dimensions_excluded_from_composite": sorted(excluded),
    }

    Path(args.output).write_text(json.dumps(output, indent=2, sort_keys=True))
    print(f"assemble_output: wrote {args.output} ({len(enriched)} candidates, top 50 emitted)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
