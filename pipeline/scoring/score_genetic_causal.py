#!/usr/bin/env python3
"""D1 — Genetic causal evidence scorer.

Combines: count of distinct relevant traits with genome-wide-significant loci
+ -log10(min p-value) weighted by sample size.
Target-agnostic: operates only on GWAS Catalog snapshot fields.
"""
from __future__ import annotations
import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scoring_lib import read_tsv, z_score, emit_scores, DATA_DIR, PIPELINE_ROOT  # noqa: E402

RELEVANT_TRAITS = {
    "bmi", "hba1c", "alt_levels", "liver_fat_fraction", "type_2_diabetes",
    "ldl_cholesterol", "triglycerides", "hdl_cholesterol", "fasting_glucose",
    "mash",
}
P_THRESHOLD = 5e-8


def main() -> int:
    universe_path = PIPELINE_ROOT / "universe" / "candidate_universe.tsv"
    gwas_path = DATA_DIR / "gwas_catalog_metabolic_loci.tsv"
    output_path = PIPELINE_ROOT / "scoring" / "_scores_D1.tsv"

    universe = read_tsv(universe_path)
    gwas = read_tsv(gwas_path)

    # Build per-gene metrics
    metrics: dict[str, dict] = {}
    for u in universe:
        eg = u["ensembl_gene_id"]
        metrics[eg] = {"trait_count": 0, "min_log_p": 0.0, "max_sample": 0}

    for r in gwas:
        eg = r.get("ensembl_gene_id", "")
        if eg not in metrics:
            continue
        try:
            p = float(r.get("p_value", "1"))
            n = int(r.get("sample_size", "0"))
        except ValueError:
            continue
        trait = r.get("trait", "").strip()
        if trait not in RELEVANT_TRAITS:
            continue
        if p < P_THRESHOLD:
            metrics[eg]["trait_count"] += 1
            log_p = -math.log10(max(p, 1e-300))
            if log_p > metrics[eg]["min_log_p"]:
                metrics[eg]["min_log_p"] = log_p
            if n > metrics[eg]["max_sample"]:
                metrics[eg]["max_sample"] = n

    # Raw composite: trait_count * sqrt(max_sample/1000) * (min_log_p / 8)
    raw: dict[str, float] = {}
    missingness: dict[str, bool] = {}
    for eg, m in metrics.items():
        n_factor = math.sqrt(max(m["max_sample"], 1) / 1000.0)
        p_factor = m["min_log_p"] / 8.0
        raw[eg] = m["trait_count"] * n_factor * p_factor
        missingness[eg] = (m["trait_count"] == 0)

    # z-score across universe
    z = z_score(raw)
    emit_scores(z, missingness, output_path, "D1_genetic_causal")
    n_covered = sum(1 for v in missingness.values() if not v)
    print(f"score_genetic_causal: wrote {output_path}; covered {n_covered}/{len(metrics)} candidates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
