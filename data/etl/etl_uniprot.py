#!/usr/bin/env python3
"""
ETL: UniProt SwissProt human reviewed dump -> snapshots_real/uniprot_protein_classes.tsv

Target-blind: derives protein_class only from UniProt keyword vocabulary and
subcellular-location comments. No gene hard-coding.

Input:
  pipeline/data_sources/raw_dumps/uniprot/human_reviewed_swissprot.dat.gz

Output schema:
  gene_symbol  ensembl_gene_id  uniprot_id  protein_class  is_secreted  signal_peptide  orf_length_bp
"""

from __future__ import annotations

import gzip
import hashlib
import re
import sys
import time
from pathlib import Path

from Bio import SwissProt
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "pipeline" / "data_sources" / "raw_dumps" / "uniprot" / \
    "human_reviewed_swissprot.dat.gz"
OUT_DIR = ROOT / "pipeline" / "data_sources" / "snapshots_real"
OUT_TSV = OUT_DIR / "uniprot_protein_classes.tsv"


def log(msg: str) -> None:
    print(f"[etl_uniprot] {msg}", file=sys.stderr, flush=True)


# --- protein_class classification rules (first match wins).
# Each rule: (predicate(kw_set, is_secreted), class_label).
# kw_set is a set of UniProt keyword strings already lowercased.
def has_kw(kws: set[str], *needles: str) -> bool:
    return any(any(n in k for k in kws) for n in needles)


CLASS_RULES = [
    # ---- secreted-family classifications (when is_secreted) ----
    ("secreted_growth_factor", lambda kw, sec: sec and has_kw(kw, "growth factor")),
    ("secreted_hormone",       lambda kw, sec: sec and has_kw(kw, "hormone")),
    ("secreted_cytokine",      lambda kw, sec: sec and has_kw(kw, "cytokine")),
    ("secreted_neuropeptide",  lambda kw, sec: sec and has_kw(kw, "neuropeptide")),
    ("secreted_apolipoprotein", lambda kw, sec: has_kw(kw, "apolipoprotein")),
    ("secreted_acute_phase",   lambda kw, sec: sec and has_kw(kw, "acute phase")),
    ("secreted_protease",      lambda kw, sec: sec and has_kw(kw, "protease", "hydrolase") and has_kw(kw, "serine", "metallo", "aspartyl", "thiol", "cysteine") is False and has_kw(kw, "protease")),
    ("secreted_enzyme",        lambda kw, sec: sec and has_kw(kw, "hydrolase", "transferase", "ligase", "oxidoreductase", "isomerase", "lyase")),
    ("secreted_transfer_protein", lambda kw, sec: sec and has_kw(kw, "lipid transport", "lipid-binding", "transport")),
    ("secreted_cofactor",      lambda kw, sec: sec and has_kw(kw, "cofactor")),
    ("secreted_precursor",     lambda kw, sec: sec and has_kw(kw, "cleavage on pair of basic residues")),
    ("secreted_peptide",       lambda kw, sec: sec and has_kw(kw, "antimicrobial", "defensin", "peptide")),
    ("secreted_protein",       lambda kw, sec: sec),
    # ---- non-secreted classifications ----
    ("gpcr",                   lambda kw, sec: has_kw(kw, "g-protein coupled receptor")),
    ("receptor_tyrosine_kinase", lambda kw, sec: has_kw(kw, "receptor tyrosine kinase") or
                                  (has_kw(kw, "tyrosine-protein kinase") and has_kw(kw, "receptor"))),
    ("receptor_guanylyl_cyclase", lambda kw, sec: has_kw(kw, "guanylate cyclase") and has_kw(kw, "receptor")),
    ("receptor_kinase",        lambda kw, sec: has_kw(kw, "receptor") and has_kw(kw, "kinase")),
    ("pseudokinase",           lambda kw, sec: has_kw(kw, "pseudokinase")),
    ("kinase",                 lambda kw, sec: has_kw(kw, "kinase")),
    ("nuclear_receptor",       lambda kw, sec: has_kw(kw, "nuclear receptor")),
    ("transcription_factor",   lambda kw, sec: has_kw(kw, "transcription factor") or
                                                (has_kw(kw, "transcription") and has_kw(kw, "dna-binding"))),
    ("coactivator",            lambda kw, sec: has_kw(kw, "coactivator", "co-activator")),
    ("ion_channel",            lambda kw, sec: has_kw(kw, "ion channel", "voltage-gated channel", "ligand-gated ion channel")),
    ("transporter",            lambda kw, sec: has_kw(kw, "symport", "antiport", "ion transport") and not has_kw(kw, "ion channel")),
    ("transport_protein",      lambda kw, sec: has_kw(kw, "transport")),
    ("rna_binding",            lambda kw, sec: has_kw(kw, "rna-binding")),
    ("lipid_droplet",          lambda kw, sec: has_kw(kw, "lipid droplet")),
    ("cofactor_protein",       lambda kw, sec: has_kw(kw, "cofactor")),
    ("cytoskeletal",           lambda kw, sec: has_kw(kw, "cytoskeleton")),
    ("structural_protein",     lambda kw, sec: has_kw(kw, "structural protein")),
    ("signaling_adapter",      lambda kw, sec: has_kw(kw, "sh2 domain", "sh3 domain", "adapter")),
    ("receptor",               lambda kw, sec: has_kw(kw, "receptor")),
    ("transfer_protein",       lambda kw, sec: has_kw(kw, "lipid transport", "lipid-binding")),
    ("enzyme",                 lambda kw, sec: has_kw(kw, "hydrolase", "transferase", "ligase", "oxidoreductase", "isomerase", "lyase", "enzyme")),
    ("membrane_protein",       lambda kw, sec: has_kw(kw, "membrane")),
    ("regulator",              lambda kw, sec: has_kw(kw, "regulator")),
]


def classify(kw_lower: set[str], is_secreted: bool) -> str:
    for label, pred in CLASS_RULES:
        try:
            if pred(kw_lower, is_secreted):
                return label
        except Exception:
            pass
    return "unknown"


_ECO_RE = re.compile(r"\s*\{[^}]*\}\s*")


def _clean_name(s: str) -> str:
    """Strip ECO evidence-code blocks ('{ECO:...}') and trailing whitespace."""
    s = _ECO_RE.sub("", s)
    return s.strip().split()[0] if s.strip() else ""


def parse_gene_symbol(gene_name_field) -> str | None:
    """gene_name is a list of dicts in BioPython >=1.80, or a string in older.

    We want the primary 'Name=' token, with evidence codes stripped.
    """
    if not gene_name_field:
        return None
    if isinstance(gene_name_field, list):
        for entry in gene_name_field:
            if isinstance(entry, dict) and "Name" in entry:
                cleaned = _clean_name(entry["Name"])
                if cleaned:
                    return cleaned
        return None
    # string form: "Name=ABC; Synonyms=DEF;"
    s = str(gene_name_field)
    m = re.search(r"Name=([^;]+)", s)
    if m:
        cleaned = _clean_name(m.group(1))
        if cleaned:
            return cleaned
    return None


_ENSG_RE = re.compile(r"(ENSG\d+)(?:\.\d+)?")


def parse_ensembl(cross_refs) -> str | None:
    """Return the first ENSG... id from Ensembl xrefs."""
    for xref in cross_refs:
        if not xref:
            continue
        if xref[0] != "Ensembl":
            continue
        for cell in xref[1:]:
            if not cell:
                continue
            m = _ENSG_RE.search(str(cell))
            if m:
                return m.group(1)
    return None


_SECRETED_RE = re.compile(r"\bSecreted\b", re.IGNORECASE)


def has_signal_peptide(features) -> bool:
    for f in features:
        ftype = getattr(f, "type", None) or (f[0] if isinstance(f, tuple) else None)
        if ftype and str(ftype).upper() == "SIGNAL":
            return True
    return False


def is_secreted(comments) -> bool:
    for c in comments:
        if not c:
            continue
        if c.startswith("SUBCELLULAR LOCATION") and _SECRETED_RE.search(c):
            return True
    return False


def main() -> int:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    seen_ensg: set[str] = set()
    total = 0
    with gzip.open(RAW, "rt") as fh:
        for rec in SwissProt.parse(fh):
            total += 1
            if total % 5000 == 0:
                log(f"  parsed {total} records...")
            # Human-only safety check (file is already human, but verify)
            if "9606" not in rec.taxonomy_id:
                continue
            gene = parse_gene_symbol(rec.gene_name)
            ensg = parse_ensembl(rec.cross_references)
            if not gene or not ensg:
                continue
            if ensg in seen_ensg:
                continue  # take first record per ENSG
            seen_ensg.add(ensg)

            kw_lower = {k.lower() for k in (rec.keywords or [])}
            secreted = is_secreted(rec.comments or [])
            sigpep = has_signal_peptide(rec.features or [])
            klass = classify(kw_lower, secreted)
            orf_bp = int(rec.sequence_length) * 3 if rec.sequence_length else 0

            rows.append({
                "gene_symbol": gene,
                "ensembl_gene_id": ensg,
                "uniprot_id": rec.accessions[0] if rec.accessions else "",
                "protein_class": klass,
                "is_secreted": secreted,
                "signal_peptide": sigpep,
                "orf_length_bp": orf_bp,
            })

    log(f"total records parsed: {total}; emitted: {len(rows)}")
    df = pd.DataFrame(rows).sort_values("gene_symbol").reset_index(drop=True)

    df.to_csv(OUT_TSV, sep="\t", index=False)
    md5 = hashlib.md5(OUT_TSV.read_bytes()).hexdigest()
    counts = df["protein_class"].value_counts().to_dict()
    with open(OUT_TSV, "a") as fh:
        fh.write(f"# md5: {md5}\n")
        for cls in sorted(counts):
            fh.write(f"# class_count[{cls}]: {counts[cls]}\n")
    log(f"wrote {OUT_TSV} ({len(df)} rows, md5={md5})")
    log(f"unique genes: {df['gene_symbol'].nunique()}; unique classes: {df['protein_class'].nunique()}")
    log(f"elapsed: {time.time()-t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
