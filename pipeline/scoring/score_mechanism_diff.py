#!/usr/bin/env python3
"""D6 — Mechanism novelty vs crowded standard-of-care classes."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scoring_lib import read_tsv, z_score, emit_scores, DATA_DIR, PIPELINE_ROOT  # noqa: E402

# Common, crowded SOC mechanism classes — these get a novelty PENALTY
CROWDED_CLASSES = {"gpcr", "kinase", "nuclear_receptor"}
# Pathway-orthogonal, less-trodden classes — bonus
NOVEL_CLASSES = {
    "secreted_growth_factor", "secreted_cytokine", "secreted_hormone",
    "secreted_peptide", "secreted_apolipoprotein", "secreted_cofactor",
}


def main() -> int:
    universe_path = PIPELINE_ROOT / "universe" / "candidate_universe.tsv"
    up_path = DATA_DIR / "uniprot_protein_classes.tsv"
    ch_path = DATA_DIR / "chembl_metabolic_targets.tsv"
    output_path = PIPELINE_ROOT / "scoring" / "_scores_D6.tsv"

    universe = read_tsv(universe_path)
    up = read_tsv(up_path)
    ch = read_tsv(ch_path)

    up_idx: dict[str, dict] = {r.get("ensembl_gene_id", ""): r for r in up}

    # Count compounds per ensembl as a proxy for crowdedness
    compound_density: dict[str, int] = {}
    for r in ch:
        eg = r.get("ensembl_gene_id", "")
        compound_density[eg] = compound_density.get(eg, 0) + 1

    raw: dict[str, float] = {}
    miss: dict[str, bool] = {}
    for u in universe:
        eg = u["ensembl_gene_id"]
        pclass = up_idx.get(eg, {}).get("protein_class", "")
        if not pclass:
            raw[eg] = 0.0
            miss[eg] = True
            continue
        miss[eg] = False
        novelty = 0.0
        if pclass in NOVEL_CLASSES:
            novelty += 1.0
        if pclass in CROWDED_CLASSES:
            novelty -= 0.5
        # Penalize high compound density (lots of competition)
        n_comp = compound_density.get(eg, 0)
        if n_comp >= 3:
            novelty -= 0.5
        elif n_comp == 0:
            novelty += 0.3
        raw[eg] = novelty

    z = z_score(raw)
    emit_scores(z, miss, output_path, "D6_mechanism_differentiation")
    print(f"score_mechanism_diff: wrote {output_path}; covered {sum(1 for v in miss.values() if not v)}/{len(raw)} candidates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
