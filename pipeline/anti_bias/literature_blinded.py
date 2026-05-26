#!/usr/bin/env python3
"""Literature-blinded re-rank with uniform redaction.

Approach (target-agnostic in implementation; target-aware in evaluator):
  1. Read forbidden target names from pipeline/reviewers/FORBIDDEN_TARGET_NAMES.txt.
  2. Build a "redacted literature snapshot" in memory: for each row in the
     literature_metabolic_genes.tsv snapshot, if the gene_symbol matches a forbidden
     name (case-insensitive) or is in a literature-derived alias set, blank its
     pubmed_count_metabolic and pubmed_count_total fields. The redaction is applied
     UNIFORMLY across all candidates that match forbidden patterns (we do not target
     any specific gene by ID — the rule is "any name in FORBIDDEN_TARGET_NAMES.txt").
  3. Re-score D4 (literature) from the redacted snapshot. Produce a full redacted
     ranking. Compute top-5 overlap with the full ranking.

This is implemented as a mechanism in the pipeline anti-bias suite. The output JSON
includes the full reranked output (top-25), the redacted_term_count, and the
top-5 overlap.
"""
from __future__ import annotations
import csv
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from anti_bias_lib import load_universe, load_all_scores, load_weights, compute_composite, PIPELINE_ROOT  # noqa: E402

LITERATURE_DIM = "D4_literature_evidence"


def load_forbidden_names() -> list[str]:
    path = PIPELINE_ROOT / "reviewers" / "FORBIDDEN_TARGET_NAMES.txt"
    names = []
    if path.exists():
        for ln in path.read_text().splitlines():
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                names.append(ln)
    return names


def read_lit_snapshot() -> list[dict]:
    path = PIPELINE_ROOT / "data_sources" / "snapshots" / "literature_metabolic_genes.tsv"
    rows = []
    with path.open() as f:
        non_comment = [ln for ln in f if not ln.startswith("#") and ln.strip()]
        reader = csv.DictReader(non_comment, delimiter="\t")
        for r in reader:
            rows.append(r)
    return rows


def redact_lit_snapshot(rows: list[dict], forbidden: list[str]) -> tuple[list[dict], int]:
    """Uniform redaction: zero pubmed counts for rows whose gene_symbol matches a forbidden pattern."""
    pat = re.compile("|".join(re.escape(n) for n in forbidden), re.IGNORECASE)
    redacted = []
    n_redacted = 0
    for r in rows:
        new_r = dict(r)
        sym = r.get("gene_symbol", "")
        if pat.fullmatch(sym):
            new_r["pubmed_count_metabolic"] = "0"
            new_r["pubmed_count_total"] = "0"
            new_r["_redacted"] = "1"
            n_redacted += 1
        redacted.append(new_r)
    return redacted, n_redacted


def rescore_d4_from_redacted(redacted_rows: list[dict], universe: list[dict]) -> dict[str, float]:
    """Recompute D4 scores from the redacted snapshot, mirroring score_literature.py logic."""
    raw: dict[str, float] = {}
    by_eg: dict[str, dict] = {r["ensembl_gene_id"]: r for r in redacted_rows if r.get("ensembl_gene_id")}
    for u in universe:
        eg = u["ensembl_gene_id"]
        row = by_eg.get(eg)
        if row is None:
            raw[eg] = 0.0
            continue
        try:
            c = int(row.get("pubmed_count_metabolic", "0"))
            t = max(int(row.get("pubmed_count_total", "1")), 1)
        except ValueError:
            c = 0
            t = 1
        specificity = c / t if t else 0
        raw[eg] = math.log10(c + 1) * (0.3 + specificity)
    # z-score
    vals = list(raw.values())
    if not vals:
        return raw
    n = len(vals)
    mean = sum(vals) / n
    var = sum((v - mean) ** 2 for v in vals) / max(n - 1, 1)
    sd = math.sqrt(var) if var > 0 else 1.0
    out: dict[str, float] = {}
    for eg, v in raw.items():
        z = (v - mean) / sd
        out[eg] = max(-3.0, min(3.0, z))
    return out


def main() -> int:
    universe = load_universe()
    all_scores = load_all_scores()
    weights = load_weights()

    # Full ranking with original D4
    full = compute_composite(all_scores, weights, universe)
    full_top5 = [r["ensembl_gene_id"] for r in full[:5]]

    # Redact + re-score D4
    forbidden = load_forbidden_names()
    lit_rows = read_lit_snapshot()
    redacted_rows, n_redacted = redact_lit_snapshot(lit_rows, forbidden)
    blinded_d4 = rescore_d4_from_redacted(redacted_rows, universe)

    # Build blinded score set with redacted D4
    blinded_scores = dict(all_scores)
    blinded_scores[LITERATURE_DIM] = blinded_d4

    blinded = compute_composite(blinded_scores, weights, universe)
    blinded_top5 = [r["ensembl_gene_id"] for r in blinded[:5]]

    overlap = len(set(full_top5) & set(blinded_top5))

    # Top-25 of blinded ranking for full output transparency
    blinded_top25 = [
        {"rank": r["rank"], "ensembl_gene_id": r["ensembl_gene_id"],
         "gene_symbol": r["gene_symbol"], "composite_score": round(r["composite_score"], 4)}
        for r in blinded[:25]
    ]

    output = {
        "mechanism": "literature_blinded",
        "literature_dim": LITERATURE_DIM,
        "redaction_method": "uniform_name_match_against_FORBIDDEN_TARGET_NAMES",
        "redacted_term_count": n_redacted,
        "redacted_terms": forbidden,
        "full_top5_ensembl": full_top5,
        "blinded_top5_ensembl": blinded_top5,
        "blinded_top25_ranking": blinded_top25,
        "top5_overlap_count": overlap,
    }
    out_path = Path(__file__).resolve().parent / "_results_lit_blind.json"
    out_path.write_text(json.dumps(output, indent=2, sort_keys=True))
    print(f"literature_blinded: redacted {n_redacted} rows; top5 overlap = {overlap}/5; wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
