#!/usr/bin/env python3
"""D5 — Secretion status and structural modulatability.

Rewards: is_secreted=True (more modality options), reasonable ORF size (300-15000bp ideal).
Target-agnostic: operates on UniProt protein-class features.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scoring_lib import read_tsv, z_score, emit_scores, DATA_DIR, PIPELINE_ROOT  # noqa: E402


def main() -> int:
    universe_path = PIPELINE_ROOT / "universe" / "candidate_universe.tsv"
    up_path = DATA_DIR / "uniprot_protein_classes.tsv"
    output_path = PIPELINE_ROOT / "scoring" / "_scores_D5.tsv"

    universe = read_tsv(universe_path)
    up = read_tsv(up_path)

    idx: dict[str, dict] = {}
    for r in up:
        idx[r.get("ensembl_gene_id", "")] = r

    raw: dict[str, float] = {}
    miss: dict[str, bool] = {}
    for u in universe:
        eg = u["ensembl_gene_id"]
        m = idx.get(eg)
        if not m:
            raw[eg] = 0.0
            miss[eg] = True
            continue
        miss[eg] = False
        is_secreted = m.get("is_secreted", "False") == "True"
        has_signal = m.get("signal_peptide", "False") == "True"
        try:
            orf = int(m.get("orf_length_bp", "0"))
        except ValueError:
            orf = 0
        # Score components
        s_secreted = 1.0 if is_secreted else 0.0
        s_signal = 0.5 if has_signal else 0.0
        # ORF score: peak around 300-3000, falls off outside
        if 300 <= orf <= 3000:
            s_orf = 1.0
        elif 3000 < orf <= 15000:
            s_orf = 0.6
        elif 100 <= orf < 300:
            s_orf = 0.4
        elif orf > 15000:
            s_orf = 0.2
        else:
            s_orf = 0.0
        raw[eg] = s_secreted + s_signal + s_orf

    z = z_score(raw)
    emit_scores(z, miss, output_path, "D5_secretion_and_modulatability")
    print(f"score_secretion_modulatability: wrote {output_path}; covered {sum(1 for v in miss.values() if not v)}/{len(raw)} candidates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
