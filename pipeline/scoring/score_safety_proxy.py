#!/usr/bin/env python3
"""D7 — Safety profile proxy.

Heuristic: restricted-expression receptor classes (e.g., secreted hormones with
narrow receptor distributions) get a SAFER score than broadly-expressed targets.
Track record from ChEMBL: high max_phase WITHOUT withdrawal record gets safer score.

For Round 0, this is a coarse proxy. Phase β can swap in real FAERS/withdrawal data.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scoring_lib import read_tsv, z_score, emit_scores, DATA_DIR, PIPELINE_ROOT  # noqa: E402

# Broad-expression classes — likely off-target risk
BROAD_CLASSES = {
    "transcription_factor", "kinase", "receptor_tyrosine_kinase",
    "enzyme", "transporter", "ion_channel",
}
# Restricted-expression / signaling-restricted classes
RESTRICTED_CLASSES = {
    "secreted_hormone", "secreted_peptide", "secreted_neuropeptide",
    "secreted_growth_factor", "secreted_cytokine",
}


def main() -> int:
    universe_path = PIPELINE_ROOT / "universe" / "candidate_universe.tsv"
    up_path = DATA_DIR / "uniprot_protein_classes.tsv"
    ch_path = DATA_DIR / "chembl_metabolic_targets.tsv"
    output_path = PIPELINE_ROOT / "scoring" / "_scores_D7.tsv"

    universe = read_tsv(universe_path)
    up_idx = {r.get("ensembl_gene_id", ""): r for r in read_tsv(up_path)}

    # Max phase per gene = positive signal (regulatory acceptance proxy)
    max_phase: dict[str, int] = {}
    for r in read_tsv(ch_path):
        eg = r.get("ensembl_gene_id", "")
        try:
            ph = int(r.get("max_phase", "0"))
        except ValueError:
            ph = 0
        if ph > max_phase.get(eg, 0):
            max_phase[eg] = ph

    raw: dict[str, float] = {}
    miss: dict[str, bool] = {}
    for u in universe:
        eg = u["ensembl_gene_id"]
        meta = up_idx.get(eg, {})
        pclass = meta.get("protein_class", "")
        if not pclass:
            raw[eg] = 0.0
            miss[eg] = True
            continue
        miss[eg] = False
        s = 0.0
        if pclass in RESTRICTED_CLASSES:
            s += 0.8
        if pclass in BROAD_CLASSES:
            s -= 0.4
        # ChEMBL phase bonus (regulatory tolerance proxy)
        s += 0.2 * max_phase.get(eg, 0)
        raw[eg] = s

    z = z_score(raw)
    emit_scores(z, miss, output_path, "D7_safety_proxy")
    print(f"score_safety_proxy: wrote {output_path}; covered {sum(1 for v in miss.values() if not v)}/{len(raw)} candidates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
