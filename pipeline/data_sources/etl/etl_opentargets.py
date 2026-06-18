#!/usr/bin/env python3
"""
ETL: OpenTargets 26.03 -> snapshots_real/opentargets_metabolic_associations.tsv

Target-blind: filters only by disease IDs / canonical disease names. No gene
hard-coding.

Input:
  pipeline/data_sources/raw_dumps/opentargets_26.03/disease.parquet
  pipeline/data_sources/raw_dumps/opentargets_26.03/target/*.parquet
  pipeline/data_sources/raw_dumps/opentargets_26.03/association_overall_direct/*.parquet

Output schema:
  gene_symbol  ensembl_gene_id  disease  association_score  evidence_count
"""

from __future__ import annotations

import glob
import hashlib
import os
import sys
import time
from pathlib import Path

import pyarrow.parquet as pq
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "pipeline" / "data_sources" / "raw_dumps" / "opentargets_26.03"
OUT_DIR = ROOT / "pipeline" / "data_sources" / "snapshots_real"
OUT_TSV = OUT_DIR / "opentargets_metabolic_associations.tsv"


# Canonical pipeline disease name -> set of OT disease IDs that should map to it.
# Selected by manual ontology inspection of disease.parquet (name match +
# canonical EFO/MONDO id confirmation). Children/descendants of these terms are
# resolved at runtime by walking the `ancestors` field.
CANONICAL_DISEASES: dict[str, set[str]] = {
    "obesity": {
        "EFO_0001073",          # obesity (root EFO term)
    },
    "type_2_diabetes": {
        "MONDO_0005148",        # type 2 diabetes mellitus
    },
    "nafld": {
        "EFO_0003095",          # non-alcoholic fatty liver disease
        "EFO_1001248",          # non-alcoholic fatty liver
    },
    "mash": {
        "EFO_1001249",          # non-alcoholic steatohepatitis (NASH/MASH)
    },
}


def log(msg: str) -> None:
    print(f"[etl_opentargets] {msg}", file=sys.stderr, flush=True)


def expand_via_descendants(seed_ids: set[str], disease_df: pd.DataFrame) -> set[str]:
    """Expand a seed of disease IDs to include all descendant IDs from the
    ontology (so e.g. obesity covers monogenic-obesity subtypes if OT has
    associations against them)."""
    seed = set(seed_ids)
    sub = disease_df[disease_df["id"].isin(seed)]
    expanded = set(seed)
    for desc_list in sub["descendants"]:
        if desc_list is not None:
            for d in desc_list:
                if d:
                    expanded.add(d)
    return expanded


def build_disease_map(disease_parquet: Path) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Return (disease_id -> canonical_name, canonical_name -> list of source IDs used)."""
    log(f"loading disease ontology: {disease_parquet}")
    tbl = pq.read_table(
        str(disease_parquet),
        columns=["id", "name", "descendants"],
    )
    df = tbl.to_pandas()
    log(f"  disease rows: {len(df)}")

    id_to_canonical: dict[str, str] = {}
    matched_source: dict[str, list[str]] = {}

    for canonical, seed in CANONICAL_DISEASES.items():
        # Verify seed IDs exist
        present_seed = [s for s in seed if s in set(df["id"])]
        missing = sorted(set(seed) - set(present_seed))
        if missing:
            log(f"  WARNING: seed IDs missing from disease.parquet for {canonical}: {missing}")
        expanded = expand_via_descendants(set(present_seed), df)
        matched_source[canonical] = sorted(expanded)
        for did in expanded:
            # if id already mapped to a different canonical, keep the more-specific
            # mapping (we process in dict insertion order; later wins for clearer logging)
            id_to_canonical[did] = canonical
        log(
            f"  canonical={canonical}: seeds={sorted(present_seed)} "
            f"expanded_total={len(expanded)}"
        )

    return id_to_canonical, matched_source


def build_target_map(target_dir: Path) -> dict[str, str]:
    """ensembl_gene_id -> approvedSymbol."""
    files = sorted(glob.glob(str(target_dir / "*.parquet")))
    log(f"loading {len(files)} target parquet files")
    parts = []
    for fp in files:
        t = pq.read_table(fp, columns=["id", "approvedSymbol"])
        parts.append(t.to_pandas())
    tgt = pd.concat(parts, ignore_index=True)
    log(f"  target rows: {len(tgt)} (unique ids: {tgt['id'].nunique()})")
    # id IS the Ensembl gene id (ENSG...)
    return dict(zip(tgt["id"], tgt["approvedSymbol"].fillna("")))


def iter_associations(assoc_dir: Path):
    files = sorted(glob.glob(str(assoc_dir / "*.parquet")))
    log(f"streaming {len(files)} association parquet files")
    for fp in files:
        t = pq.read_table(
            fp,
            columns=["diseaseId", "targetId", "associationScore", "evidenceCount"],
        )
        yield fp, t.to_pandas()


def main() -> int:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    id_to_canonical, matched_source = build_disease_map(RAW / "disease.parquet")
    matched_ids = set(id_to_canonical.keys())
    log(f"total disease IDs after expansion: {len(matched_ids)}")

    target_map = build_target_map(RAW / "target")

    keep_rows = []
    total_rows = 0
    for fp, df in iter_associations(RAW / "association_overall_direct"):
        total_rows += len(df)
        df = df[df["diseaseId"].isin(matched_ids)]
        if df.empty:
            continue
        df = df.assign(
            canonical=df["diseaseId"].map(id_to_canonical),
            gene_symbol=df["targetId"].map(target_map),
        )
        df = df[df["gene_symbol"].astype(bool)]  # drop unmapped/empty symbol
        keep_rows.append(df)
    log(f"streamed total association rows: {total_rows}")

    if not keep_rows:
        log("ERROR: no associations matched any canonical disease.")
        return 1

    full = pd.concat(keep_rows, ignore_index=True)
    log(f"rows after disease filter: {len(full)}")

    # Dedupe (gene, canonical) by max score; sum evidenceCount across redundant
    # source diseases to retain breadth signal.
    grouped = (
        full.groupby(["gene_symbol", "targetId", "canonical"], as_index=False)
        .agg(association_score=("associationScore", "max"),
             evidence_count=("evidenceCount", "sum"))
    )

    out = grouped.rename(
        columns={"targetId": "ensembl_gene_id", "canonical": "disease"}
    )[["gene_symbol", "ensembl_gene_id", "disease", "association_score", "evidence_count"]]

    # Round score for stability across hash comparisons
    out["association_score"] = out["association_score"].astype(float).round(6)
    out = out.sort_values(["gene_symbol", "disease"]).reset_index(drop=True)

    # Write TSV
    out.to_csv(OUT_TSV, sep="\t", index=False, float_format="%.6f")
    # Compute md5 of TSV body (exclude footer) and append footer comment.
    md5 = hashlib.md5(OUT_TSV.read_bytes()).hexdigest()
    with open(OUT_TSV, "a") as fh:
        fh.write(f"# md5: {md5}\n")
        for canonical, ids in matched_source.items():
            fh.write(f"# source_ids[{canonical}]: {','.join(sorted(ids))}\n")
    log(f"wrote {OUT_TSV} ({len(out)} rows, md5={md5})")
    log(f"unique genes: {out['gene_symbol'].nunique()}; unique diseases: {out['disease'].nunique()}")
    log(f"elapsed: {time.time()-t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
