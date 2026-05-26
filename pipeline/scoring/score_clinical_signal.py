#!/usr/bin/env python3
"""D2 — Clinical / pharmacological signal scorer.

Combines: max ChEMBL clinical phase + number of distinct mechanisms + breadth across indications.
Target-agnostic.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scoring_lib import read_tsv, z_score, emit_scores, DATA_DIR, PIPELINE_ROOT  # noqa: E402


def main() -> int:
    universe_path = PIPELINE_ROOT / "universe" / "candidate_universe.tsv"
    chembl_path = DATA_DIR / "chembl_metabolic_targets.tsv"
    output_path = PIPELINE_ROOT / "scoring" / "_scores_D2.tsv"

    universe = read_tsv(universe_path)
    chembl = read_tsv(chembl_path)

    metrics: dict[str, dict] = {}
    for u in universe:
        metrics[u["ensembl_gene_id"]] = {
            "max_phase": 0,
            "mechanisms": set(),
            "indications": set(),
        }

    for r in chembl:
        eg = r.get("ensembl_gene_id", "")
        if eg not in metrics:
            continue
        try:
            phase = int(r.get("max_phase", "0"))
        except ValueError:
            phase = 0
        if phase > metrics[eg]["max_phase"]:
            metrics[eg]["max_phase"] = phase
        metrics[eg]["mechanisms"].add(r.get("mechanism", "").strip())
        metrics[eg]["indications"].add(r.get("indication", "").strip())

    raw: dict[str, float] = {}
    miss: dict[str, bool] = {}
    for eg, m in metrics.items():
        raw[eg] = m["max_phase"] + 0.3 * len(m["mechanisms"]) + 0.2 * len(m["indications"])
        miss[eg] = (m["max_phase"] == 0)

    z = z_score(raw)
    emit_scores(z, miss, output_path, "D2_clinical_signal")
    print(f"score_clinical_signal: wrote {output_path}; covered {sum(1 for v in miss.values() if not v)}/{len(metrics)} candidates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
