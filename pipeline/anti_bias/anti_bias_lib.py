"""Shared utilities for anti-bias mechanisms."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

PIPELINE_ROOT = Path(__file__).resolve().parent.parent


def load_universe() -> list[dict]:
    path = PIPELINE_ROOT / "universe" / "candidate_universe.tsv"
    rows = []
    with path.open() as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            rows.append(r)
    return rows


def load_score_tsv(path: Path) -> dict[str, float]:
    """Load a per-dimension score TSV into {ensembl: score}."""
    out: dict[str, float] = {}
    with path.open() as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            eg = r["ensembl_gene_id"]
            score_col = next((k for k in r if k.startswith("score_")), None)
            if score_col is None:
                continue
            try:
                out[eg] = float(r[score_col])
            except ValueError:
                out[eg] = 0.0
    return out


def load_all_scores() -> dict[str, dict[str, float]]:
    """Returns {dimension_id: {ensembl: score}} for all dimensions."""
    scoring_dir = PIPELINE_ROOT / "scoring"
    all_scores: dict[str, dict[str, float]] = {}
    for p in sorted(scoring_dir.glob("_scores_*.tsv")):
        # Filename: _scores_D1_genetic_causal.tsv OR _scores_D1.tsv
        # Extract dim id from header column
        with p.open() as f:
            header = f.readline().strip().split("\t")
            dim_col = next((c for c in header if c.startswith("score_")), None)
            if dim_col is None:
                continue
            dim_id = dim_col[len("score_"):]
        all_scores[dim_id] = load_score_tsv(p)
    return all_scores


def load_weights() -> dict[str, float]:
    path = PIPELINE_ROOT / "scoring" / "weights.json"
    doc = json.loads(path.read_text())
    return doc["weights"]


def compute_composite(all_scores: dict[str, dict[str, float]], weights: dict[str, float],
                       universe: list[dict]) -> list[dict]:
    """Compute weighted composite score per candidate. Returns sorted list of dicts."""
    out = []
    for u in universe:
        eg = u["ensembl_gene_id"]
        composite = 0.0
        for dim, w in weights.items():
            score = all_scores.get(dim, {}).get(eg, 0.0)
            composite += w * score
        out.append({
            "ensembl_gene_id": eg,
            "gene_symbol": u.get("gene_symbol", ""),
            "composite_score": composite,
        })
    out.sort(key=lambda r: -r["composite_score"])
    for rank, r in enumerate(out, start=1):
        r["rank"] = rank
    return out
