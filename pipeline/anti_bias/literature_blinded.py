#!/usr/bin/env python3
"""Literature-blinded re-rank.

Proxy approach (target-agnostic): set the literature dimension's contribution to zero
(equivalent to redacting all literature-derived signal uniformly across candidates).
Compare top-5 overlap with full ranking.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from anti_bias_lib import load_universe, load_all_scores, load_weights, compute_composite  # noqa: E402

LITERATURE_DIM = "D4_literature_evidence"


def main() -> int:
    universe = load_universe()
    all_scores = load_all_scores()
    weights = load_weights()

    # Full ranking
    full = compute_composite(all_scores, weights, universe)
    full_top5 = [r["ensembl_gene_id"] for r in full[:5]]

    # Blinded: zero out literature dimension scores
    blinded_scores = dict(all_scores)
    if LITERATURE_DIM in blinded_scores:
        blinded_scores[LITERATURE_DIM] = {k: 0.0 for k in blinded_scores[LITERATURE_DIM]}

    blinded = compute_composite(blinded_scores, weights, universe)
    blinded_top5 = [r["ensembl_gene_id"] for r in blinded[:5]]

    overlap = len(set(full_top5) & set(blinded_top5))

    output = {
        "mechanism": "literature_blinded",
        "literature_dim": LITERATURE_DIM,
        "full_top5_ensembl": full_top5,
        "blinded_top5_ensembl": blinded_top5,
        "top5_overlap_count": overlap,
        "note": "Proxy: zero the literature dim. Full literature NER redaction is a Phase β refinement.",
    }
    out_path = Path(__file__).resolve().parent / "_results_lit_blind.json"
    out_path.write_text(json.dumps(output, indent=2, sort_keys=True))
    print(f"literature_blinded: wrote {out_path}; top5 overlap = {overlap}/5")
    return 0


if __name__ == "__main__":
    sys.exit(main())
