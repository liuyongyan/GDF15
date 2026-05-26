#!/usr/bin/env python3
"""Negative-control ranking distribution.

Reads NC list from thresholds.json (target-agnostic — these are known-failed metabolic targets).
Reports percentile of each NC in the full ranking.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from anti_bias_lib import load_universe, load_all_scores, load_weights, compute_composite  # noqa: E402


def main() -> int:
    thresholds = json.loads((Path(__file__).resolve().parent / "thresholds.json").read_text())
    nc_symbols = set(thresholds["negative_controls"]["controls"])

    universe = load_universe()
    all_scores = load_all_scores()
    weights = load_weights()
    ranking = compute_composite(all_scores, weights, universe)
    n = len(ranking)

    sym_to_rank = {r["gene_symbol"]: r["rank"] for r in ranking}
    results = []
    # Sort to ensure deterministic ordering across runs (sets are unordered)
    for sym in sorted(nc_symbols):
        rank = sym_to_rank.get(sym)
        if rank is None:
            results.append({"control": sym, "rank": None, "percentile": None, "note": "not in universe"})
        else:
            percentile = (rank / n) * 100.0
            results.append({"control": sym, "rank": rank, "percentile": percentile})

    output = {
        "mechanism": "negative_controls",
        "universe_size": n,
        "controls": results,
        "mean_percentile_of_controls": sum((r.get("percentile") or 0) for r in results) / max(len(results), 1),
    }
    out_path = Path(__file__).resolve().parent / "_results_nc.json"
    out_path.write_text(json.dumps(output, indent=2, sort_keys=True))
    print(f"negative_controls: wrote {out_path}; mean NC percentile = {output['mean_percentile_of_controls']:.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
