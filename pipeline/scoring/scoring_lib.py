"""Shared utilities for per-dimension scoring scripts."""
from __future__ import annotations

import csv
import math
from pathlib import Path

PIPELINE_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PIPELINE_ROOT / "data_sources" / "snapshots"


def read_tsv(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(str(path))
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        non_comment = [ln for ln in f if not ln.startswith("#") and ln.strip()]
        reader = csv.DictReader(non_comment, delimiter="\t")
        for r in reader:
            rows.append(r)
    return rows


def load_universe(universe_path: Path) -> list[dict]:
    return read_tsv(universe_path)


def z_score(values: dict[str, float]) -> dict[str, float]:
    """Convert raw values to z-scores; clamp to [-3.0, 3.0]."""
    if not values:
        return {}
    vals = list(values.values())
    n = len(vals)
    mean = sum(vals) / n
    var = sum((v - mean) ** 2 for v in vals) / max(n - 1, 1)
    sd = math.sqrt(var) if var > 0 else 1.0
    out: dict[str, float] = {}
    for k, v in values.items():
        z = (v - mean) / sd
        out[k] = max(-3.0, min(3.0, z))
    return out


def emit_scores(scores: dict[str, float], missingness: dict[str, bool],
                output_path: Path, dimension_id: str) -> None:
    """Write per-candidate scores to TSV with columns: ensembl_gene_id, score, missingness_flag."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["ensembl_gene_id", f"score_{dimension_id}", f"missingness_{dimension_id}"])
        for ensembl in sorted(scores.keys()):
            writer.writerow([
                ensembl,
                f"{scores[ensembl]:.6f}",
                "1" if missingness.get(ensembl, False) else "0",
            ])
