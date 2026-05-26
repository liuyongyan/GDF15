#!/usr/bin/env python3
"""LOO ablation: re-rank with each dimension removed; report stability."""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from anti_bias_lib import load_universe, load_all_scores, load_weights, compute_composite  # noqa: E402


def main() -> int:
    universe = load_universe()
    all_scores = load_all_scores()
    weights = load_weights()

    # Full ranking
    full = compute_composite(all_scores, weights, universe)
    full_top5_eg = [r["ensembl_gene_id"] for r in full[:5]]

    results: dict[str, dict] = {}
    for dim in weights:
        # Re-weight: redistribute removed weight equally among remaining
        remaining = {k: v for k, v in weights.items() if k != dim}
        renorm_factor = 1.0 / sum(remaining.values())
        renorm = {k: v * renorm_factor for k, v in remaining.items()}
        ranking = compute_composite(all_scores, renorm, universe)
        # Compute rank changes for original top 5
        ablation_ranks = {r["ensembl_gene_id"]: r["rank"] for r in ranking}
        changes = []
        for eg in full_top5_eg:
            original = next(r["rank"] for r in full if r["ensembl_gene_id"] == eg)
            new = ablation_ranks.get(eg, len(universe))
            changes.append({"ensembl": eg, "original_rank": original, "new_rank": new, "delta": new - original})
        results[dim] = {
            "removed_dim": dim,
            "top5_after_ablation": [{"ensembl": r["ensembl_gene_id"], "rank": r["rank"], "score": r["composite_score"]} for r in ranking[:5]],
            "original_top5_rank_changes": changes,
            "mean_abs_rank_change_top5": sum(abs(c["delta"]) for c in changes) / 5.0,
        }

    avg_across_dims = sum(r["mean_abs_rank_change_top5"] for r in results.values()) / len(results)
    output = {
        "mechanism": "loo_ablation",
        "full_top5_ensembl": full_top5_eg,
        "per_dim_results": results,
        "aggregate_mean_rank_change": avg_across_dims,
    }
    out_path = Path(__file__).resolve().parent / "_results_loo.json"
    out_path.write_text(json.dumps(output, indent=2, sort_keys=True))
    print(f"loo_ablation: wrote {out_path}; aggregate mean rank change = {avg_across_dims:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
