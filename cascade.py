#!/usr/bin/env python3
"""5-layer constraint cascade for saRNA-deliverable secreted-protein target selection.

Cascade:
  L1 — Modality compatibility   : secreted + 60bp ≤ ORF ≤ 4500bp (saRNA payload)
  L2 — Disease evidence         : OT score ≥ 0.05 OR ≥1 GWAS hit OR ≥50 PubMed
  L3 — Druggability             : protein_class ∈ {hormone, growth_factor,
                                  cytokine, peptide, neuropeptide} (signaling)
  L4 — Opportunity ranking      : evidence / (1 + max_clinical_phase)
  L5 — Safety baseline          : not in known-clinical-failure list

Data inputs (all under data/snapshots_real/ and data/raw_dumps/):
  - opentargets_metabolic_associations.tsv (Open Targets 26.03)
  - gwas_catalog_metabolic_loci.tsv         (NHGRI-EBI GWAS Catalog)
  - uniprot_protein_classes.tsv             (UniProt SwissProt human reviewed)
  - literature_metabolic_genes.tsv          (PubMed via NCBI E-utilities)
  - raw_dumps/chembl/chembl_metabolic_api_subset.tsv (ChEMBL REST by indication)

Usage:
    python3 cascade.py [--gene GENE]   # default: show top 30 + obesity-only top 30
"""
from __future__ import annotations
import argparse
import csv
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
DATA = REPO / "data" / "snapshots_real"
CHEMBL = REPO / "data" / "raw_dumps" / "chembl" / "chembl_metabolic_api_subset.tsv"


# =========================================================================
# Cascade configuration
# =========================================================================
L1_MIN_ORF_BP = 60
L1_MAX_ORF_BP = 4500          # saRNA payload constraint

L2_MIN_OT_SCORE = 0.05        # any of {obesity, T2D, NAFLD, MASH}
L2_MIN_PUBMED = 50            # metabolic-context PubMed citations

# L3 — only directly-druggable signaling classes (not enzymes/transport/structural)
L3_DRUGGABLE_CLASSES = {
    'secreted_hormone',         # classic endocrine (insulin, leptin, GDF15 etc.)
    'secreted_growth_factor',   # paracrine/endocrine signaling (FGF21, BDNF, BMP*)
    'secreted_cytokine',        # immune/inflammatory signaling
    'secreted_peptide',         # short-peptide signaling
    'secreted_neuropeptide',    # CNS signaling
}

L4_PUBMED_WEIGHT = 0.1        # how much log10(pubmed+1) adds to evidence
L4_GWAS_WEIGHT = 0.5          # bonus per GWAS hit (capped at 10)

# L5 — exclude known clinical failures
L5_KNOWN_FAILURES = {
    "CETP",   # torcetrapib/evacetrapib/anacetrapib all failed
    "CNR1",   # rimonabant withdrawn (psychiatric AEs)
    "HTR2C",  # lorcaserin withdrawn (CV/cancer signal)
    "DGAT1",  # multiple Phase 2 failures
}


# =========================================================================
# Data loading
# =========================================================================
def read_tsv(p: Path) -> list[dict]:
    rows = []
    with p.open() as f:
        clean = [ln for ln in f if not ln.startswith("#") and ln.strip()]
        for r in csv.DictReader(clean, delimiter="\t"):
            rows.append(r)
    return rows


def load_data():
    """Load all 5 real public-data sources."""
    if not DATA.exists():
        sys.exit(f"ERROR: data directory not found at {DATA}")
    ot = read_tsv(DATA / "opentargets_metabolic_associations.tsv")
    gwas = read_tsv(DATA / "gwas_catalog_metabolic_loci.tsv")
    uniprot = read_tsv(DATA / "uniprot_protein_classes.tsv")
    lit = read_tsv(DATA / "literature_metabolic_genes.tsv")
    chembl = read_tsv(CHEMBL) if CHEMBL.exists() else []

    uniprot_by_gene = {r['gene_symbol']: r for r in uniprot if r.get('gene_symbol')}
    lit_by_gene = {r['gene_symbol']: r for r in lit if r.get('gene_symbol')}

    ot_by_gene: dict[str, dict[str, float]] = {}
    for r in ot:
        g = r.get('gene_symbol')
        if not g:
            continue
        try:
            s = float(r.get('association_score', 0))
        except ValueError:
            s = 0.0
        d = r.get('disease', '?')
        ot_by_gene.setdefault(g, {})[d] = max(ot_by_gene.get(g, {}).get(d, 0), s)

    gwas_by_gene: dict[str, list[str]] = {}
    for r in gwas:
        g = r.get('gene_symbol')
        if g:
            gwas_by_gene.setdefault(g, []).append(r.get('trait', '?'))

    chembl_max_phase: dict[str, int] = {}
    for r in chembl:
        g = r.get('gene_symbol')
        if not g:
            continue
        try:
            ph = int(float(r.get('max_phase', 0) or 0))
        except ValueError:
            ph = 0
        chembl_max_phase[g] = max(chembl_max_phase.get(g, 0), ph)

    return {
        'uniprot': uniprot_by_gene,
        'lit': lit_by_gene,
        'ot': ot_by_gene,
        'gwas': gwas_by_gene,
        'chembl_phase': chembl_max_phase,
    }


# =========================================================================
# Cascade layers
# =========================================================================
def L1(gene: str, db) -> bool:
    """Modality compatibility: secreted + ORF size fits saRNA payload."""
    up = db['uniprot'].get(gene)
    if not up:
        return False
    if up.get('is_secreted', 'False') != 'True':
        return False
    try:
        orf = int(up.get('orf_length_bp', 0))
    except ValueError:
        orf = 0
    return L1_MIN_ORF_BP <= orf <= L1_MAX_ORF_BP


def L2(gene: str, db) -> bool:
    """Disease evidence: OT, GWAS, or PubMed metabolic-context."""
    ot_scores = db['ot'].get(gene, {})
    if ot_scores and max(ot_scores.values()) >= L2_MIN_OT_SCORE:
        return True
    if gene in db['gwas']:
        return True
    if gene in db['lit']:
        try:
            pm = int(db['lit'][gene].get('pubmed_count_metabolic', 0))
        except ValueError:
            pm = 0
        if pm >= L2_MIN_PUBMED:
            return True
    return False


def L3(gene: str, db) -> bool:
    """Druggability: restricted to directly-druggable signaling classes."""
    pc = db['uniprot'].get(gene, {}).get('protein_class', 'unknown')
    return pc in L3_DRUGGABLE_CLASSES


def L5(gene: str, db) -> bool:
    """Safety baseline: exclude known clinical failures."""
    return gene not in L5_KNOWN_FAILURES


def opportunity(gene: str, db) -> tuple[float, float, int, float, int, int]:
    """Layer 4 ranking: evidence / (1 + max_clinical_phase)."""
    ot_sum = sum(db['ot'].get(gene, {}).values())
    gwas_n = len(db['gwas'].get(gene, []))
    pm = 0
    if gene in db['lit']:
        try:
            pm = int(db['lit'][gene].get('pubmed_count_metabolic', 0))
        except ValueError:
            pm = 0
    evidence = (ot_sum
                + L4_GWAS_WEIGHT * min(gwas_n, 10)
                + L4_PUBMED_WEIGHT * math.log10(pm + 1))
    phase = db['chembl_phase'].get(gene, 0)
    opp = evidence / (1 + phase)
    return opp, evidence, phase, ot_sum, gwas_n, pm


# =========================================================================
# Main
# =========================================================================
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gene", default=None,
                    help="Show cascade trace for this gene only.")
    args = ap.parse_args()

    db = load_data()
    universe = set(db['uniprot'].keys())
    l1 = {g for g in universe if L1(g, db)}
    l2 = {g for g in l1 if L2(g, db)}
    l3 = {g for g in l2 if L3(g, db)}
    l5 = {g for g in l3 if L5(g, db)}

    print(f"Cascade: {len(universe)} -> L1={len(l1)} -> L2={len(l2)} -> L3={len(l3)} -> L5={len(l5)}")

    # Obesity-specific
    obesity = set()
    for g in l5:
        if db['ot'].get(g, {}).get('obesity', 0) >= L2_MIN_OT_SCORE:
            obesity.add(g)
        elif any(t == 'bmi' for t in db['gwas'].get(g, [])):
            obesity.add(g)
    print(f"Obesity-specific subset: {len(obesity)}")

    # Single-gene trace mode
    if args.gene:
        g = args.gene
        print(f"\n=== Cascade trace for {g} ===")
        for layer, name, fn in [(1, "modality", L1), (2, "disease evidence", L2),
                                  (3, "druggability", L3), (5, "safety", L5)]:
            ok = fn(g, db)
            print(f"  L{layer} {name:<20}: {'✓ PASS' if ok else '✗ FAIL'}")
        if g in l5:
            opp, ev, ph, ot_s, gw, pm = opportunity(g, db)
            scored = sorted(l5, key=lambda x: -opportunity(x, db)[0])
            rank_full = scored.index(g) + 1
            scored_obes = sorted(obesity, key=lambda x: -opportunity(x, db)[0])
            rank_obes = scored_obes.index(g) + 1 if g in obesity else None
            print(f"  L4 opportunity = {opp:.3f}")
            print(f"  Full rank: #{rank_full} of {len(l5)}")
            if rank_obes:
                print(f"  Obesity rank: #{rank_obes} of {len(obesity)}")
            print(f"  Details: OT_sum={ot_s:.3f} GWAS={gw} PubMed_metabolic={pm} max_phase={ph}")
        return 0

    # Full ranking output
    scored = [(g, *opportunity(g, db)) for g in l5]
    scored.sort(key=lambda x: -x[1])

    print(f"\n{'='*100}")
    print(f"TOP 30 — full cascade-admissible (by opportunity index)")
    print(f"{'='*100}")
    print(f"{'#':<4} {'Gene':<12} {'Opp':>6} {'Evid':>5} {'Ph':>3} {'OTsum':>5} {'GWAS':>5} {'PubMed':>6} {'Class':<25}")
    for i, (g, opp, ev, ph, ot_s, gw, pm) in enumerate(scored[:30], 1):
        pc = db['uniprot'].get(g, {}).get('protein_class', '?')
        print(f"{i:<4} {g:<12} {opp:>6.2f} {ev:>5.2f} {ph:>3} {ot_s:>5.2f} {gw:>5} {pm:>6} {pc:<25}")

    scored_obes = sorted([(g, *opportunity(g, db)) for g in obesity], key=lambda x: -x[1])
    print(f"\n{'='*100}")
    print(f"TOP 30 — obesity-specific (OT obesity ≥ 0.05 OR ≥1 BMI GWAS hit)")
    print(f"{'='*100}")
    print(f"{'#':<4} {'Gene':<12} {'Opp':>6} {'OT_obes':>7} {'BMI_GWAS':>9} {'PubMed':>6} {'Class':<25}")
    for i, (g, opp, ev, ph, ot_s, gw, pm) in enumerate(scored_obes[:30], 1):
        pc = db['uniprot'].get(g, {}).get('protein_class', '?')
        ot_obes = db['ot'].get(g, {}).get('obesity', 0)
        bmi_n = sum(1 for t in db['gwas'].get(g, []) if t == 'bmi')
        print(f"{i:<4} {g:<12} {opp:>6.2f} {ot_obes:>7.2f} {bmi_n:>9} {pm:>6} {pc:<25}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
