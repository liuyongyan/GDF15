#!/usr/bin/env python3
"""Permutation test for top-candidate significance.

Null distribution: shuffle each dimension's scores independently across candidates
(preserving marginal distributions), recompute composite, and record the top candidate's
composite score. Repeat N times. The empirical p-value for the observed top candidate
is the fraction of permuted runs with a top composite score >= observed.

This is target-agnostic: the test asks "could a random shuffle produce a top score as
high as the observed?" without referencing any specific gene.
"""
from __future__ import annotations
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from anti_bias_lib import load_universe, load_all_scores, load_weights, compute_composite  # noqa: E402

N_PERMUTATIONS = 1000  # Round 0 default; configurable in Phase β
SEED = 42  # deterministic for reproducibility


def main() -> int:
    universe = load_universe()
    all_scores = load_all_scores()
    weights = load_weights()

    full = compute_composite(all_scores, weights, universe)
    observed_top_score = full[0]["composite_score"]
    observed_top_ensembl = full[0]["ensembl_gene_id"]

    rng = random.Random(SEED)
    # Build score arrays per dim
    universe_ids = [u["ensembl_gene_id"] for u in universe]
    null_top_scores = []
    for _ in range(N_PERMUTATIONS):
        perm_scores: dict[str, dict[str, float]] = {}
        for dim, scores in all_scores.items():
            vals = [scores.get(eg, 0.0) for eg in universe_ids]
            rng.shuffle(vals)
            perm_scores[dim] = dict(zip(universe_ids, vals))
        perm_ranking = compute_composite(perm_scores, weights, universe)
        null_top_scores.append(perm_ranking[0]["composite_score"])

    # Empirical p-value: fraction of null tops >= observed top
    ge_count = sum(1 for v in null_top_scores if v >= observed_top_score)
    p_value = (ge_count + 1) / (N_PERMUTATIONS + 1)  # add-one smoothing

    output = {
        "mechanism": "permutation_test",
        "n_permutations": N_PERMUTATIONS,
        "seed": SEED,
        "observed_top_ensembl": observed_top_ensembl,
        "observed_top_composite_score": observed_top_score,
        "empirical_p_value": p_value,
        "null_top_score_quantiles": {
            "min": min(null_top_scores),
            "q25": sorted(null_top_scores)[N_PERMUTATIONS // 4],
            "median": sorted(null_top_scores)[N_PERMUTATIONS // 2],
            "q75": sorted(null_top_scores)[3 * N_PERMUTATIONS // 4],
            "max": max(null_top_scores),
        },
    }
    out_path = Path(__file__).resolve().parent / "_results_perm.json"
    out_path.write_text(json.dumps(output, indent=2, sort_keys=True))
    print(f"permutation_test: wrote {out_path}; p={p_value:.4f} (n={N_PERMUTATIONS})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
