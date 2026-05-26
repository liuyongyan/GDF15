#!/usr/bin/env python3
"""D4 — Literature evidence (log-scaled to avoid hot-topic dominance)."""
from __future__ import annotations
import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scoring_lib import read_tsv, z_score, emit_scores, DATA_DIR, PIPELINE_ROOT  # noqa: E402


def main() -> int:
    universe_path = PIPELINE_ROOT / "universe" / "candidate_universe.tsv"
    lit_path = DATA_DIR / "literature_metabolic_genes.tsv"
    output_path = PIPELINE_ROOT / "scoring" / "_scores_D4.tsv"

    universe = read_tsv(universe_path)
    lit = read_tsv(lit_path)

    counts: dict[str, int] = {}
    totals: dict[str, int] = {}
    for r in lit:
        eg = r.get("ensembl_gene_id", "")
        try:
            counts[eg] = int(r.get("pubmed_count_metabolic", "0"))
            totals[eg] = int(r.get("pubmed_count_total", "1"))
        except ValueError:
            continue

    raw: dict[str, float] = {}
    miss: dict[str, bool] = {}
    for u in universe:
        eg = u["ensembl_gene_id"]
        c = counts.get(eg, 0)
        t = max(totals.get(eg, 1), 1)
        # log10(c+1) * (c/t): metabolic specificity weighted by log-scale magnitude
        specificity = c / t
        raw[eg] = math.log10(c + 1) * (0.3 + specificity)
        miss[eg] = (c == 0)

    z = z_score(raw)
    emit_scores(z, miss, output_path, "D4_literature_evidence")
    print(f"score_literature: wrote {output_path}; covered {sum(1 for v in miss.values() if not v)}/{len(raw)} candidates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
