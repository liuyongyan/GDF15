#!/usr/bin/env python3
"""
ETL: GWAS Catalog full associations TSV -> snapshots_real/gwas_catalog_metabolic_loci.tsv

Target-blind: filters only by EFO trait URI / MAPPED_TRAIT text / p-value
threshold. No gene hard-coding.

Input:
  pipeline/data_sources/raw_dumps/gwas_catalog/gwas-catalog-associations_ontology-annotated-full.tsv

Output schema:
  gene_symbol  ensembl_gene_id  trait  lead_snp  p_value  beta  sample_size
"""

from __future__ import annotations

import hashlib
import re
import sys
import time
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "pipeline" / "data_sources" / "raw_dumps" / "gwas_catalog" / \
    "gwas-catalog-associations_ontology-annotated-full.tsv"
OUT_DIR = ROOT / "pipeline" / "data_sources" / "snapshots_real"
OUT_TSV = OUT_DIR / "gwas_catalog_metabolic_loci.tsv"


# Canonical pipeline trait name -> EFO/MONDO URI fragments (lowercase substring
# match on MAPPED_TRAIT_URI) and MAPPED_TRAIT text fragments (lowercase substring
# match). Either URI or text must match for the row to qualify.
CANONICAL_TRAITS: dict[str, dict[str, list[str]]] = {
    "bmi": {
        "uri": ["efo_0004340"],
        "text": ["body mass index"],
    },
    "hba1c": {
        "uri": ["efo_0004541"],
        "text": ["hba1c", "hemoglobin a1c", "glycated haemoglobin", "glycated hemoglobin"],
    },
    "alt_levels": {
        "uri": ["efo_0004734"],
        "text": ["alanine aminotransferase"],
    },
    "liver_fat_fraction": {
        "uri": ["efo_0010068"],
        "text": ["liver fat", "hepatic fat", "liver iron"],
    },
    "type_2_diabetes": {
        "uri": ["mondo_0005148"],
        "text": ["type 2 diabetes", "type ii diabetes"],
    },
    "ldl_cholesterol": {
        "uri": ["efo_0004611"],
        "text": ["low density lipoprotein cholesterol", "ldl cholesterol"],
    },
    "triglycerides": {
        "uri": ["efo_0004530"],
        "text": ["triglyceride"],
    },
    "hdl_cholesterol": {
        "uri": ["efo_0004612"],
        "text": ["high density lipoprotein cholesterol", "hdl cholesterol"],
    },
    "fasting_glucose": {
        "uri": ["efo_0004465"],
        "text": ["fasting blood glucose", "fasting glucose", "fasting plasma glucose"],
    },
    "mash": {
        "uri": ["efo_1001249", "mondo_0004790"],
        "text": ["non-alcoholic steatohepatitis", "nonalcoholic steatohepatitis",
                 "nash", "mash"],
    },
}


P_THRESH = 5e-8


def log(msg: str) -> None:
    print(f"[etl_gwas_catalog] {msg}", file=sys.stderr, flush=True)


def parse_pvalue(s: str) -> float | None:
    """Parse a p-value cell which may be like '1E-150' or '5e-08'."""
    if s is None or s == "" or pd.isna(s):
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def parse_float(s: str) -> float | None:
    if s is None or s == "" or pd.isna(s):
        return None
    s = str(s).strip()
    # Sometimes OR/BETA is text like "0.31 [0.28-0.34]" — take leading number
    m = re.match(r"^[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", s)
    if not m:
        return None
    try:
        return float(m.group(0))
    except ValueError:
        return None


_SAMPLE_NUM_RE = re.compile(r"([\d,]+)")


def parse_sample_size(s: str) -> int | None:
    if s is None or pd.isna(s) or s == "":
        return None
    s = str(s)
    # Sum all comma-separated numbers in the description string. This handles
    # multi-cohort descriptions like "200,000 Europeans, 50,000 African Americans".
    total = 0
    any_match = False
    for m in _SAMPLE_NUM_RE.finditer(s):
        tok = m.group(1).replace(",", "")
        if tok.isdigit():
            n = int(tok)
            # ignore obvious year tokens (1900-2099)
            if 1900 <= n <= 2099:
                continue
            total += n
            any_match = True
    return total if any_match else None


_RSID_RE = re.compile(r"(rs\d+)", re.IGNORECASE)


def parse_lead_snp(s: str) -> str | None:
    if s is None or pd.isna(s) or s == "":
        return None
    m = _RSID_RE.search(str(s))
    if m:
        return m.group(1).lower()
    # Fallback: take the SNP token verbatim, trimming risk allele suffix
    tok = str(s).split(",")[0].split(";")[0].strip()
    return tok or None


def first_nonempty(s: str) -> str | None:
    if s is None or pd.isna(s) or s == "":
        return None
    parts = re.split(r"[,;]\s*", str(s))
    for p in parts:
        p = p.strip()
        if p and p.lower() not in ("na", "n/a", "-"):
            return p
    return None


def match_trait(mapped_trait: str, mapped_uri: str) -> str | None:
    """Return canonical trait name if the row matches any canonical, else None."""
    if mapped_trait is None or (isinstance(mapped_trait, float) and pd.isna(mapped_trait)):
        mapped_trait = ""
    if mapped_uri is None or (isinstance(mapped_uri, float) and pd.isna(mapped_uri)):
        mapped_uri = ""
    mt = str(mapped_trait).lower()
    mu = str(mapped_uri).lower()
    for canonical, spec in CANONICAL_TRAITS.items():
        if any(u in mu for u in spec["uri"]):
            return canonical
        # require word-boundary safety on short text tokens to avoid e.g. "nash"
        # matching inside other words; for longer phrases substring is fine.
        for t in spec["text"]:
            if len(t) <= 4:
                if re.search(r"\b" + re.escape(t) + r"\b", mt):
                    return canonical
            else:
                if t in mt:
                    return canonical
    return None


def main() -> int:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    log(f"loading {RAW}")
    cols = [
        "DISEASE/TRAIT",
        "INITIAL SAMPLE SIZE",
        "MAPPED_GENE",
        "REPORTED GENE(S)",
        "SNP_GENE_IDS",
        "STRONGEST SNP-RISK ALLELE",
        "SNPS",
        "P-VALUE",
        "OR or BETA",
        "MAPPED_TRAIT",
        "MAPPED_TRAIT_URI",
    ]
    df = pd.read_csv(
        RAW,
        sep="\t",
        dtype=str,
        low_memory=False,
        usecols=cols,
        on_bad_lines="skip",
    )
    log(f"  rows read: {len(df)}")

    # Parse p-value first; filter by threshold to shrink working set early.
    df["_p"] = df["P-VALUE"].apply(parse_pvalue)
    sig = df[df["_p"].notna() & (df["_p"] < P_THRESH)].copy()
    log(f"  rows with p<{P_THRESH:g}: {len(sig)}")

    # Assign canonical trait
    sig["_trait"] = [
        match_trait(mt, mu)
        for mt, mu in zip(sig["MAPPED_TRAIT"], sig["MAPPED_TRAIT_URI"])
    ]
    sig = sig[sig["_trait"].notna()].copy()
    log(f"  rows after canonical-trait filter: {len(sig)}")

    # Extract output fields
    sig["gene_symbol"] = sig["MAPPED_GENE"].apply(first_nonempty)
    # Fallback to REPORTED GENE(S) when MAPPED_GENE missing
    fallback = sig["REPORTED GENE(S)"].apply(first_nonempty)
    sig["gene_symbol"] = sig["gene_symbol"].fillna(fallback)
    sig["ensembl_gene_id"] = sig["SNP_GENE_IDS"].apply(first_nonempty)
    sig["lead_snp"] = sig["SNPS"].apply(parse_lead_snp)
    if sig["lead_snp"].isna().any():
        # Try STRONGEST SNP-RISK ALLELE as fallback
        fb = sig["STRONGEST SNP-RISK ALLELE"].apply(parse_lead_snp)
        sig["lead_snp"] = sig["lead_snp"].fillna(fb)
    sig["beta"] = sig["OR or BETA"].apply(parse_float)
    sig["sample_size"] = sig["INITIAL SAMPLE SIZE"].apply(parse_sample_size)

    # Drop rows missing essential fields (need at least gene_symbol + lead_snp).
    before = len(sig)
    sig = sig[sig["gene_symbol"].notna() & sig["lead_snp"].notna()].copy()
    log(f"  rows after gene+SNP non-null filter: {len(sig)} (dropped {before-len(sig)})")

    # If ensembl_gene_id is missing, leave it empty (downstream may lookup).
    sig["ensembl_gene_id"] = sig["ensembl_gene_id"].fillna("")

    out = sig.rename(columns={"_p": "p_value", "_trait": "trait"})[
        ["gene_symbol", "ensembl_gene_id", "trait", "lead_snp",
         "p_value", "beta", "sample_size"]
    ]

    # Dedupe by (ensembl_gene_id || gene_symbol, trait, lead_snp); keep lowest p_value.
    out["_dedup_key"] = out["ensembl_gene_id"].where(
        out["ensembl_gene_id"] != "", out["gene_symbol"]
    )
    out = (
        out.sort_values("p_value")
        .drop_duplicates(subset=["_dedup_key", "trait", "lead_snp"], keep="first")
        .drop(columns=["_dedup_key"])
    )

    # Final ordering: gene_symbol, trait, p_value
    out = out.sort_values(["gene_symbol", "trait", "p_value"]).reset_index(drop=True)

    # Format p_value with scientific notation, beta as float
    def fmt_p(p):
        return f"{p:.3e}" if pd.notna(p) else ""

    def fmt_beta(b):
        return f"{b:.4g}" if pd.notna(b) else ""

    def fmt_n(n):
        return str(int(n)) if pd.notna(n) else ""

    out_fmt = out.copy()
    out_fmt["p_value"] = out_fmt["p_value"].apply(fmt_p)
    out_fmt["beta"] = out_fmt["beta"].apply(fmt_beta)
    out_fmt["sample_size"] = out_fmt["sample_size"].apply(fmt_n)

    out_fmt.to_csv(OUT_TSV, sep="\t", index=False)
    md5 = hashlib.md5(OUT_TSV.read_bytes()).hexdigest()
    with open(OUT_TSV, "a") as fh:
        fh.write(f"# md5: {md5}\n")
        for canonical in CANONICAL_TRAITS:
            n = int((out["trait"] == canonical).sum())
            fh.write(f"# trait_count[{canonical}]: {n}\n")
    log(f"wrote {OUT_TSV} ({len(out)} rows, md5={md5})")
    log(f"unique genes: {out['gene_symbol'].nunique()}; unique traits: {out['trait'].nunique()}")
    log(f"elapsed: {time.time()-t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
