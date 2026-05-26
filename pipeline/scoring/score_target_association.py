#!/usr/bin/env python3
"""D3 — Disease association breadth and strength (Open Targets)."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scoring_lib import read_tsv, z_score, emit_scores, DATA_DIR, PIPELINE_ROOT  # noqa: E402

RELEVANT_DISEASES = {"obesity", "type_2_diabetes", "nafld", "mash"}


def main() -> int:
    universe_path = PIPELINE_ROOT / "universe" / "candidate_universe.tsv"
    ot_path = DATA_DIR / "opentargets_metabolic_associations.tsv"
    output_path = PIPELINE_ROOT / "scoring" / "_scores_D3.tsv"

    universe = read_tsv(universe_path)
    ot = read_tsv(ot_path)

    metrics: dict[str, dict] = {}
    for u in universe:
        metrics[u["ensembl_gene_id"]] = {
            "diseases": {},  # disease -> max score
            "total_evidence": 0,
        }

    for r in ot:
        eg = r.get("ensembl_gene_id", "")
        if eg not in metrics:
            continue
        disease = r.get("disease", "").strip()
        if disease not in RELEVANT_DISEASES:
            continue
        try:
            score = float(r.get("association_score", "0"))
            ec = int(r.get("evidence_count", "0"))
        except ValueError:
            continue
        m = metrics[eg]
        prev = m["diseases"].get(disease, 0)
        if score > prev:
            m["diseases"][disease] = score
        m["total_evidence"] += ec

    raw: dict[str, float] = {}
    miss: dict[str, bool] = {}
    for eg, m in metrics.items():
        n_dis = len(m["diseases"])
        sum_score = sum(m["diseases"].values())
        # composite: average score across covered diseases * sqrt(disease breadth)
        avg = (sum_score / n_dis) if n_dis else 0.0
        breadth = (n_dis ** 0.5) if n_dis else 0.0
        raw[eg] = avg * breadth
        miss[eg] = (n_dis == 0)

    z = z_score(raw)
    emit_scores(z, miss, output_path, "D3_target_association_breadth")
    print(f"score_target_association: wrote {output_path}; covered {sum(1 for v in miss.values() if not v)}/{len(metrics)} candidates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
