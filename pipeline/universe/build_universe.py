#!/usr/bin/env python3
"""Deterministic, target-agnostic candidate universe builder.

Reads cached snapshots from pipeline/data_sources/snapshots/ and produces
pipeline/universe/candidate_universe.tsv via union over documented inclusion rules.

Inclusion rules (target-AGNOSTIC; same rule applied to all candidates):
  R1: Open Targets association score >= 0.50 for any of {obesity, type_2_diabetes,
      nafld, mash}
  R2: GWAS Catalog locus at genome-wide significance (p < 5e-8) for any of
      {bmi, hba1c, alt_levels, liver_fat_fraction, type_2_diabetes,
       ldl_cholesterol, triglycerides, hdl_cholesterol, fasting_glucose,
       mash}
  R3: ChEMBL target of any compound with max_phase >= 2 in {type_2_diabetes,
      obesity, nafld, mash, dyslipidemia, muscle_wasting, cachexia,
      heart_failure, cardiovascular, hpa_obesity}
  R4: Literature curation: pubmed_count_metabolic >= 50 (rule-based threshold)

The universe is the UNION across rules R1-R4, deduplicated by ensembl_gene_id.

Output: TSV with columns:
  ensembl_gene_id, gene_symbol, included_via_R1, included_via_R2, included_via_R3,
  included_via_R4, protein_class, is_secreted, orf_length_bp

Determinism:
  - Input snapshot file paths are fixed
  - Sort order: ensembl_gene_id ascending
  - SHA256 of output is reproducible from same inputs
"""

from __future__ import annotations

import csv
import hashlib
import os
import sys
from pathlib import Path


PIPELINE_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PIPELINE_ROOT / "data_sources" / "snapshots"
UNIVERSE_DIR = PIPELINE_ROOT / "universe"

SNAPSHOT_PATHS = {
    "opentargets": DATA_DIR / "opentargets_metabolic_associations.tsv",
    "gwas": DATA_DIR / "gwas_catalog_metabolic_loci.tsv",
    "chembl": DATA_DIR / "chembl_metabolic_targets.tsv",
    "literature": DATA_DIR / "literature_metabolic_genes.tsv",
    "uniprot": DATA_DIR / "uniprot_protein_classes.tsv",
}

OPEN_TARGETS_SCORE_THRESHOLD = 0.50
OPEN_TARGETS_RELEVANT_DISEASES = {"obesity", "type_2_diabetes", "nafld", "mash"}
GWAS_P_THRESHOLD = 5e-8
GWAS_RELEVANT_TRAITS = {
    "bmi", "hba1c", "alt_levels", "liver_fat_fraction", "type_2_diabetes",
    "ldl_cholesterol", "triglycerides", "hdl_cholesterol", "fasting_glucose",
    "mash",
}
CHEMBL_MIN_PHASE = 2
CHEMBL_RELEVANT_INDICATIONS = {
    "type_2_diabetes", "obesity", "nafld", "mash", "dyslipidemia",
    "muscle_wasting", "cachexia", "heart_failure", "cardiovascular",
    "hpa_obesity",
}
LITERATURE_MIN_PUBMED_METABOLIC = 50


def read_tsv(path: Path) -> list[dict]:
    """Read a TSV with a header row, skip comment lines starting with #."""
    if not path.exists():
        raise FileNotFoundError(f"snapshot missing: {path}")
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        non_comment = [ln for ln in f if not ln.startswith("#") and ln.strip()]
        reader = csv.DictReader(non_comment, delimiter="\t")
        for r in reader:
            rows.append(r)
    return rows


def select_via_opentargets(rows: list[dict]) -> set[str]:
    """Rule R1: Open Targets association score above threshold for relevant disease."""
    selected: set[str] = set()
    for r in rows:
        try:
            score = float(r["association_score"])
        except (KeyError, ValueError):
            continue
        disease = r.get("disease", "").strip()
        ensembl = r.get("ensembl_gene_id", "").strip()
        if not ensembl:
            continue
        if score >= OPEN_TARGETS_SCORE_THRESHOLD and disease in OPEN_TARGETS_RELEVANT_DISEASES:
            selected.add(ensembl)
    return selected


def select_via_gwas(rows: list[dict]) -> set[str]:
    """Rule R2: GWAS Catalog locus at genome-wide significance for relevant trait."""
    selected: set[str] = set()
    for r in rows:
        try:
            p_value = float(r["p_value"])
        except (KeyError, ValueError):
            continue
        trait = r.get("trait", "").strip()
        ensembl = r.get("ensembl_gene_id", "").strip()
        if not ensembl:
            continue
        if p_value < GWAS_P_THRESHOLD and trait in GWAS_RELEVANT_TRAITS:
            selected.add(ensembl)
    return selected


def select_via_chembl(rows: list[dict]) -> set[str]:
    """Rule R3: ChEMBL target of compound with max_phase >= MIN_PHASE in relevant indication."""
    selected: set[str] = set()
    for r in rows:
        try:
            max_phase = int(r["max_phase"])
        except (KeyError, ValueError):
            continue
        indication = r.get("indication", "").strip()
        ensembl = r.get("ensembl_gene_id", "").strip()
        if not ensembl:
            continue
        if max_phase >= CHEMBL_MIN_PHASE and indication in CHEMBL_RELEVANT_INDICATIONS:
            selected.add(ensembl)
    return selected


def select_via_literature(rows: list[dict]) -> set[str]:
    """Rule R4: literature curation by metabolic-specific pubmed count threshold."""
    selected: set[str] = set()
    for r in rows:
        try:
            count = int(r["pubmed_count_metabolic"])
        except (KeyError, ValueError):
            continue
        ensembl = r.get("ensembl_gene_id", "").strip()
        if not ensembl:
            continue
        if count >= LITERATURE_MIN_PUBMED_METABOLIC:
            selected.add(ensembl)
    return selected


def load_uniprot_index(rows: list[dict]) -> dict[str, dict]:
    """Index UniProt protein-class annotations by ensembl_gene_id."""
    index: dict[str, dict] = {}
    for r in rows:
        ensembl = r.get("ensembl_gene_id", "").strip()
        if not ensembl:
            continue
        index[ensembl] = {
            "gene_symbol": r.get("gene_symbol", ""),
            "protein_class": r.get("protein_class", ""),
            "is_secreted": r.get("is_secreted", "False"),
            "orf_length_bp": r.get("orf_length_bp", "0"),
        }
    return index


def gene_symbol_for(ensembl: str, opentargets_rows: list[dict],
                    gwas_rows: list[dict], chembl_rows: list[dict],
                    literature_rows: list[dict], uniprot_idx: dict[str, dict]) -> str:
    """Recover gene_symbol with priority: uniprot > literature > opentargets > gwas > chembl."""
    if ensembl in uniprot_idx and uniprot_idx[ensembl]["gene_symbol"]:
        return uniprot_idx[ensembl]["gene_symbol"]
    for src in (literature_rows, opentargets_rows, gwas_rows, chembl_rows):
        for r in src:
            if r.get("ensembl_gene_id") == ensembl and r.get("gene_symbol"):
                return r["gene_symbol"]
    return ""


def diversity_check(rows: list[dict]) -> tuple[bool, dict]:
    """AC-3: at least 3 distinct UniProt-derived protein classes each contributing >5%."""
    if not rows:
        return False, {"error": "empty universe"}
    n = len(rows)
    class_counts: dict[str, int] = {}
    for r in rows:
        c = r.get("protein_class", "").strip() or "unknown"
        class_counts[c] = class_counts.get(c, 0) + 1
    qualifying = {c: cnt for c, cnt in class_counts.items() if cnt / n > 0.05}
    return (len(qualifying) >= 3), {
        "total": n,
        "all_classes": class_counts,
        "qualifying_above_5pct": qualifying,
    }


def main(argv: list[str]) -> int:
    if len(argv) > 1 and argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0

    output_path = UNIVERSE_DIR / "candidate_universe.tsv"

    # Verify all snapshots are present (AC-3 Negative test: empty data_sources/ -> explicit error)
    missing = [name for name, p in SNAPSHOT_PATHS.items() if not p.exists()]
    if missing:
        print(f"build_universe: ERROR - required snapshots missing: {missing}", file=sys.stderr)
        print("build_universe: refusing to build empty universe; populate pipeline/data_sources/snapshots/", file=sys.stderr)
        return 2

    # Load all snapshots
    ot_rows = read_tsv(SNAPSHOT_PATHS["opentargets"])
    gw_rows = read_tsv(SNAPSHOT_PATHS["gwas"])
    ch_rows = read_tsv(SNAPSHOT_PATHS["chembl"])
    lt_rows = read_tsv(SNAPSHOT_PATHS["literature"])
    up_rows = read_tsv(SNAPSHOT_PATHS["uniprot"])

    print(f"build_universe: loaded snapshots: "
          f"opentargets={len(ot_rows)}, gwas={len(gw_rows)}, chembl={len(ch_rows)}, "
          f"literature={len(lt_rows)}, uniprot={len(up_rows)}")

    # Apply inclusion rules
    r1 = select_via_opentargets(ot_rows)
    r2 = select_via_gwas(gw_rows)
    r3 = select_via_chembl(ch_rows)
    r4 = select_via_literature(lt_rows)

    print(f"build_universe: R1 (OpenTargets score>={OPEN_TARGETS_SCORE_THRESHOLD}): {len(r1)} genes")
    print(f"build_universe: R2 (GWAS p<{GWAS_P_THRESHOLD}): {len(r2)} genes")
    print(f"build_universe: R3 (ChEMBL max_phase>={CHEMBL_MIN_PHASE}): {len(r3)} genes")
    print(f"build_universe: R4 (Literature pubmed_metabolic>={LITERATURE_MIN_PUBMED_METABOLIC}): {len(r4)} genes")

    # Union
    universe_ids = sorted(r1 | r2 | r3 | r4)
    print(f"build_universe: universe size (union, dedup): {len(universe_ids)} genes")

    # Build uniprot index for annotation
    uniprot_idx = load_uniprot_index(up_rows)

    # Compose output rows
    out_rows: list[dict] = []
    for ensembl in universe_ids:
        gene_symbol = gene_symbol_for(ensembl, ot_rows, gw_rows, ch_rows, lt_rows, uniprot_idx)
        uniprot_meta = uniprot_idx.get(ensembl, {})
        out_rows.append({
            "ensembl_gene_id": ensembl,
            "gene_symbol": gene_symbol,
            "included_via_R1": "1" if ensembl in r1 else "0",
            "included_via_R2": "1" if ensembl in r2 else "0",
            "included_via_R3": "1" if ensembl in r3 else "0",
            "included_via_R4": "1" if ensembl in r4 else "0",
            "protein_class": uniprot_meta.get("protein_class", "unknown"),
            "is_secreted": uniprot_meta.get("is_secreted", "False"),
            "orf_length_bp": uniprot_meta.get("orf_length_bp", "0"),
        })

    # Diversity check (AC-3)
    diversity_ok, diversity_info = diversity_check(out_rows)
    print(f"build_universe: diversity check: ok={diversity_ok}")
    print(f"build_universe: diversity info: {diversity_info}")

    # Write output
    UNIVERSE_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "ensembl_gene_id", "gene_symbol",
        "included_via_R1", "included_via_R2", "included_via_R3", "included_via_R4",
        "protein_class", "is_secreted", "orf_length_bp",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for r in out_rows:
            writer.writerow(r)

    # Determinism: compute SHA256 of output
    sha = hashlib.sha256()
    sha.update(output_path.read_bytes())
    print(f"build_universe: wrote {output_path} ({len(out_rows)} rows)")
    print(f"build_universe: output SHA256: {sha.hexdigest()}")

    # Diagnostics file
    diag = UNIVERSE_DIR / "universe_build_diagnostics.json"
    import json
    diag.write_text(json.dumps({
        "universe_size": len(out_rows),
        "rule_counts": {"R1": len(r1), "R2": len(r2), "R3": len(r3), "R4": len(r4)},
        "diversity_check_pass": diversity_ok,
        "diversity_info": diversity_info,
        "output_sha256": sha.hexdigest(),
    }, indent=2, sort_keys=True))

    if not diversity_ok:
        print("build_universe: WARNING - diversity check failed (AC-3 lower-bound violation)", file=sys.stderr)
        return 3  # non-fatal but flagged

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
