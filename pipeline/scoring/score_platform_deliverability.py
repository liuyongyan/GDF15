#!/usr/bin/env python3
"""D8 — Platform deliverability (saRNA + sublingual microneedle).

EXCLUDED from composite ranking. Consumed only by post-hoc check (post_hoc/platform_compatibility.py).
Rules (target-agnostic):
  - is_secreted=True (required for circulation-active modality)
  - orf_length_bp <= 15000 (saRNA payload size limit)
  - signal_peptide=True (further evidence of secretory pathway)
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scoring_lib import read_tsv, z_score, emit_scores, DATA_DIR, PIPELINE_ROOT  # noqa: E402


def main() -> int:
    universe_path = PIPELINE_ROOT / "universe" / "candidate_universe.tsv"
    up_path = DATA_DIR / "uniprot_protein_classes.tsv"
    output_path = PIPELINE_ROOT / "scoring" / "_scores_D8.tsv"

    universe = read_tsv(universe_path)
    up_idx = {r.get("ensembl_gene_id", ""): r for r in read_tsv(up_path)}

    raw: dict[str, float] = {}
    miss: dict[str, bool] = {}
    for u in universe:
        eg = u["ensembl_gene_id"]
        meta = up_idx.get(eg)
        if not meta:
            raw[eg] = 0.0
            miss[eg] = True
            continue
        miss[eg] = False
        is_secreted = meta.get("is_secreted", "False") == "True"
        has_signal = meta.get("signal_peptide", "False") == "True"
        try:
            orf = int(meta.get("orf_length_bp", "0"))
        except ValueError:
            orf = 0
        score = 0.0
        if is_secreted:
            score += 1.0
        if has_signal:
            score += 0.3
        if 100 <= orf <= 15000:
            score += 0.5
        elif orf > 15000:
            score -= 1.0
        raw[eg] = score

    z = z_score(raw)
    emit_scores(z, miss, output_path, "D8_platform_deliverability")
    print(f"score_platform_deliverability: wrote {output_path}; covered {sum(1 for v in miss.values() if not v)}/{len(raw)} candidates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
