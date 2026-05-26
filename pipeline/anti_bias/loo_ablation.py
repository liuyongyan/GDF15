#!/usr/bin/env python3
"""LOO ablation: re-rank with each dimension removed; report stability."""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from anti_bias_lib import load_universe, load_all_scores, load_weights, compute_composite  # noqa: E402


def spearman_rank_correlation(rank_a: dict[str, int], rank_b: dict[str, int]) -> float:
    """Spearman rank correlation over the intersection of keys."""
    keys = sorted(set(rank_a.keys()) & set(rank_b.keys()))
    n = len(keys)
    if n < 2:
        return 0.0
    a = [rank_a[k] for k in keys]
    b = [rank_b[k] for k in keys]
    # sum of squared rank differences
    d2 = sum((x - y) ** 2 for x, y in zip(a, b))
    return 1.0 - (6.0 * d2) / (n * (n * n - 1))


def main() -> int:
    universe = load_universe()
    all_scores = load_all_scores()
    weights = load_weights()

    # Full ranking
    full = compute_composite(all_scores, weights, universe)
    full_top5_eg = [r["ensembl_gene_id"] for r in full[:5]]
    full_rank_by_eg = {r["ensembl_gene_id"]: r["rank"] for r in full}

    results: dict[str, dict] = {}
    for dim in weights:
        # Re-weight: redistribute removed weight equally among remaining
        remaining = {k: v for k, v in weights.items() if k != dim}
        renorm_factor = 1.0 / sum(remaining.values())
        renorm = {k: v * renorm_factor for k, v in remaining.items()}
        ranking = compute_composite(all_scores, renorm, universe)
        ablation_ranks = {r["ensembl_gene_id"]: r["rank"] for r in ranking}
        # Top-5 rank changes
        changes = []
        for eg in full_top5_eg:
            original = next(r["rank"] for r in full if r["ensembl_gene_id"] == eg)
            new = ablation_ranks.get(eg, len(universe))
            changes.append({"ensembl": eg, "original_rank": original, "new_rank": new, "delta": new - original})
        # Spearman rank correlation across the full universe
        rho = spearman_rank_correlation(full_rank_by_eg, ablation_ranks)
        results[dim] = {
            "removed_dim": dim,
            "top5_after_ablation": [{"ensembl": r["ensembl_gene_id"], "rank": r["rank"], "score": r["composite_score"]} for r in ranking[:5]],
            "original_top5_rank_changes": changes,
            "mean_abs_rank_change_top5": sum(abs(c["delta"]) for c in changes) / 5.0,
            "spearman_rank_correlation_with_full": rho,
        }

    avg_across_dims = sum(r["mean_abs_rank_change_top5"] for r in results.values()) / len(results)
    mean_rho = sum(r["spearman_rank_correlation_with_full"] for r in results.values()) / len(results)
    output = {
        "mechanism": "loo_ablation",
        "full_top5_ensembl": full_top5_eg,
        "per_dim_results": results,
        "aggregate_mean_rank_change": avg_across_dims,
        "aggregate_mean_spearman_rho": mean_rho,
    }
    out_path = Path(__file__).resolve().parent / "_results_loo.json"
    out_path.write_text(json.dumps(output, indent=2, sort_keys=True))
    print(f"loo_ablation: wrote {out_path}; aggregate mean rank change = {avg_across_dims:.2f}; mean Spearman ρ = {mean_rho:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
