#!/usr/bin/env python3
"""6-layer constraint cascade for saRNA-deliverable secreted-protein target selection.

Cascade (5 gates then 1 ranker — execution order = layer number):
  L1 — Modality compatibility   : secreted + 60bp ≤ ORF ≤ 4500bp (saRNA payload)
  L2 — Disease evidence         : OT score ≥ 0.05 OR ≥1 GWAS hit OR ≥50 PubMed.
                                  L2 is *indication-parameterized*: the scope of
                                  diseases/traits considered is set by the
                                  --indication flag (default metabolic = all 4
                                  conditions; obesity / t2d / mash narrow to a
                                  single indication).
  L3 — Druggability             : protein_class ∈ {hormone, growth_factor,
                                  cytokine, peptide, neuropeptide} (signaling)
  L4 — Safety baseline (audit)  : confirms historical clinical failures (CETP,
                                  CNR1, HTR2C, DGAT1) are already excluded by
                                  upstream layers (vacuous-by-design for our
                                  modality; documents that as a finding)
  L5 — Expert deliverability    : manual curation catching 4 saRNA-specific
                                  failure modes that L1's coarse modality
                                  filter does not detect:
                                    (a) native plasma half-life too short
                                    (b) requires tissue-specific PC1/2 cleavage
                                    (c) obligate heterodimer (multi-ORF)
                                    (d) misclassified as signaling secreted
  L6 — Opportunity ranking      : evidence / (1 + max_clinical_phase), applied
                                  to the L5 admissible set. Indication-scoped
                                  (sums OT and counts GWAS only over the chosen
                                  indication). This is the only layer that
                                  produces a score and ordering; L1-L5 are
                                  boolean gates.

Data inputs (all under data/snapshots_real/ and data/raw_dumps/):
  - opentargets_metabolic_associations.tsv (Open Targets 26.03)
  - gwas_catalog_metabolic_loci.tsv         (NHGRI-EBI GWAS Catalog)
  - uniprot_protein_classes.tsv             (UniProt SwissProt human reviewed)
  - literature_metabolic_genes.tsv          (PubMed via NCBI E-utilities)
  - raw_dumps/chembl/chembl_metabolic_api_subset.tsv (ChEMBL REST by indication)

Usage:
    python3 cascade.py                           # default --indication metabolic
    python3 cascade.py --indication obesity      # obesity-scoped L2 + L6
    python3 cascade.py --indication obesity --gene GDF15   # single-gene trace
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

L6_PUBMED_WEIGHT = 0.1        # how much log10(pubmed+1) adds to evidence
L6_GWAS_WEIGHT = 0.5          # bonus per GWAS hit (capped at 10)

# Indication scopes for L2 evidence gating and L4 opportunity ranking.
# Each scope defines (a) the Open Targets disease names that count toward
# evidence and (b) the GWAS Catalog trait names that count toward GWAS hits.
# 'use_pubmed': PubMed counts in our snapshot are metabolic-context aggregated
# (across all 4 indications), so PubMed only meaningfully applies to the
# 'metabolic' scope; for single-indication scopes it would over-count.
INDICATION_SCOPES = {
    'metabolic': {
        'ot_diseases': {'obesity', 'type_2_diabetes', 'nafld', 'mash'},
        'gwas_traits': None,    # None means "any metabolic GWAS trait"
        'use_pubmed': True,
    },
    'obesity': {
        'ot_diseases': {'obesity'},
        'gwas_traits': {'bmi'},
        'use_pubmed': False,
    },
    't2d': {
        'ot_diseases': {'type_2_diabetes'},
        'gwas_traits': {'type_2_diabetes', 'fasting_glucose', 'hba1c'},
        'use_pubmed': False,
    },
    'mash': {
        'ot_diseases': {'nafld', 'mash'},
        'gwas_traits': {'mash', 'liver_fat_fraction', 'alt_levels'},
        'use_pubmed': False,
    },
}

# L4 — historical clinical-failure audit (confirmatory; not an active filter for
# our modality because all four are non-secreted GPCRs/enzymes or non-signaling
# secreted transport proteins, which L1+L3 already exclude). Documented here so
# the cascade can prove it considered them.
L4_KNOWN_FAILURES = {
    "CETP",   # torcetrapib/evacetrapib/anacetrapib all failed; secreted but
              # protein_class=secreted_lipid_transport → excluded at L3
    "CNR1",   # rimonabant withdrawn (psychiatric AEs); GPCR → excluded at L1
    "HTR2C",  # lorcaserin withdrawn (CV/cancer signal); GPCR → excluded at L1
    "DGAT1",  # multiple Phase 2 failures; ER membrane enzyme → excluded at L1
}

# L5 — expert deliverability curation. L1 only checks structural modality
# compatibility (secreted + ORF size). The following failure modes require
# pharmacology/cell-biology knowledge not present in our 5 public databases.
# Each entry includes the failure-mode tag for audit traceability.
L5_EXPERT_EXCLUSIONS = {
    # ---- (a) native plasma half-life too short for saRNA-sustained therapy ----
    # saRNA delivers steady-state expression over days; clearance faster than
    # ~30 min means the steady-state plasma concentration cannot reach the
    # therapeutic window regardless of expression rate. All clinical programs
    # against these targets use chemically-modified (Fc-fusion, lipidated, or
    # PEGylated) analogs that the saRNA modality cannot encode.
    "FGF21": "short_half_life",       # native t½ ~30 min in humans
    "CCK":   "short_half_life",       # cleared in minutes
    "PYY":   "short_half_life",       # PYY3-36 t½ ~8-15 min
    "GIP":   "short_half_life",       # native t½ ~7 min
    "GCG":   "short_half_life",       # glucagon ~5 min; GLP-1 ~2 min
    "GHRL":  "short_half_life",       # ghrelin ~30 min

    # ---- (b) requires tissue-specific PC1/2 (or other convertase) cleavage ----
    # Prohormone → active peptide cleavage requires PC1/PC2 (PCSK1/PCSK2),
    # which are expressed only in specialized neuroendocrine cells. Mucosal
    # cells producing saRNA-encoded protein cannot perform this processing.
    "POMC":   "prohormone_processing",   # → α-MSH, β-endorphin, ACTH
    "PCSK1N": "prohormone_processing",   # proSAAS
    "INS":    "prohormone_processing",   # → insulin (also β-cell-specific PC1/2)
    "IAPP":   "prohormone_processing",   # amylin (needs PC1/2 + amidation)
    "GAST":   "prohormone_processing",   # gastrin
    "NPY":    "prohormone_processing",   # neuropeptide Y
    "AGRP":   "prohormone_processing",   # agouti-related peptide

    # ---- (c) obligate heterodimer; single-ORF expression yields no function ----
    # Two-subunit cytokines/growth-factors require co-expression of both
    # chains in the same cell at matched stoichiometry. saRNA encodes one ORF;
    # multi-cistronic saRNA constructs exist but are an open engineering
    # problem outside the current platform scope.
    "IL12A": "heterodimer_required",   # p35 (pairs with IL12B in IL-12)
    "IL12B": "heterodimer_required",   # p40 (shared by IL-12 and IL-23)
    "IL23A": "heterodimer_required",   # p19 (pairs with IL12B in IL-23)
    "EBI3":  "heterodimer_required",   # subunit of IL-27 and IL-35
    "IL27":  "heterodimer_required",   # p28 (pairs with EBI3 to form IL-27)
    "INHBC": "heterodimer_required",   # inhibin βC; activin-C homodimer activity unclear
    "INHBE": "heterodimer_required",   # inhibin βE; activin-E pharmacology immature

    # ---- (d) misclassified by UniProt as secreted-signaling ----
    # Annotation pipelines flag these as "secreted" because they can be
    # detected extracellularly, but their primary biological role is not as
    # an extracellular signaling ligand. Treating them as drug-target cargos
    # is biologically inappropriate.
    "MAPT":  "misclassified_secreted",  # tau — intracellular microtubule binding
    "HMGB1": "misclassified_secreted",  # nuclear chromatin DAMP only when released
    "LTBP3": "misclassified_secreted",  # latent TGFβ scaffold, not a ligand
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


def L2(gene: str, db, scope) -> bool:
    """Disease evidence within the chosen indication scope: OT, GWAS, or
    (metabolic-scope-only) PubMed."""
    ot_scores = db['ot'].get(gene, {})
    relevant_ot = [s for d, s in ot_scores.items() if d in scope['ot_diseases']]
    if relevant_ot and max(relevant_ot) >= L2_MIN_OT_SCORE:
        return True
    gene_traits = db['gwas'].get(gene, [])
    if scope['gwas_traits'] is None:
        if gene_traits:
            return True
    else:
        if any(t in scope['gwas_traits'] for t in gene_traits):
            return True
    if scope['use_pubmed'] and gene in db['lit']:
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


def L4(gene: str, db) -> bool:
    """Safety baseline audit: exclude historical clinical failures.

    Note: For our modality this layer is structurally vacuous because all 4
    historical metabolic failures are non-secreted GPCRs/enzymes (L1) or
    non-signaling transport proteins (L3). The vacuity is itself a finding
    worth documenting — saRNA modality avoids the chemistries that produced
    most historical metabolic failures.
    """
    return gene not in L4_KNOWN_FAILURES


def L5(gene: str, db) -> bool:
    """Expert deliverability curation: exclude 4 saRNA-specific failure modes
    that L1's coarse modality filter does not detect (see L5_EXPERT_EXCLUSIONS
    dict for per-gene rationale)."""
    return gene not in L5_EXPERT_EXCLUSIONS


def L6_opportunity(gene: str, db, scope) -> tuple[float, float, int, float, int, int]:
    """Layer 6 ranking: evidence / (1 + max_clinical_phase), indication-scoped.

    This is the only cascade layer that produces a score rather than a boolean.
    Applied to the L5 admissible set. Sums OT scores only over the scope's
    diseases; counts GWAS hits only over the scope's traits; uses PubMed only
    when scope's use_pubmed is True.
    """
    ot_scores = db['ot'].get(gene, {})
    ot_sum = sum(s for d, s in ot_scores.items() if d in scope['ot_diseases'])
    gene_traits = db['gwas'].get(gene, [])
    if scope['gwas_traits'] is None:
        gwas_n = len(gene_traits)
    else:
        gwas_n = sum(1 for t in gene_traits if t in scope['gwas_traits'])
    pm = 0
    if scope['use_pubmed'] and gene in db['lit']:
        try:
            pm = int(db['lit'][gene].get('pubmed_count_metabolic', 0))
        except ValueError:
            pm = 0
    evidence = (ot_sum
                + L6_GWAS_WEIGHT * min(gwas_n, 10)
                + L6_PUBMED_WEIGHT * math.log10(pm + 1))
    phase = db['chembl_phase'].get(gene, 0)
    opp = evidence / (1 + phase)
    return opp, evidence, phase, ot_sum, gwas_n, pm


# =========================================================================
# Main
# =========================================================================
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--indication", default="metabolic",
                    choices=sorted(INDICATION_SCOPES.keys()),
                    help="Indication scope for L2 evidence gating and L4 "
                         "opportunity ranking (default: metabolic, all 4 "
                         "indications combined).")
    ap.add_argument("--gene", default=None,
                    help="Show cascade trace for this gene only.")
    args = ap.parse_args()

    scope = INDICATION_SCOPES[args.indication]
    print(f"Indication scope: {args.indication}  "
          f"(OT diseases: {sorted(scope['ot_diseases'])}, "
          f"GWAS traits: {sorted(scope['gwas_traits']) if scope['gwas_traits'] else 'any metabolic'}, "
          f"PubMed: {'used' if scope['use_pubmed'] else 'not used'})")

    db = load_data()
    universe = set(db['uniprot'].keys())
    l1 = {g for g in universe if L1(g, db)}
    l2 = {g for g in l1 if L2(g, db, scope)}
    l3 = {g for g in l2 if L3(g, db)}
    l4 = {g for g in l3 if L4(g, db)}
    l5 = {g for g in l4 if L5(g, db)}

    print(f"Cascade (gates): {len(universe)} -> L1={len(l1)} -> L2={len(l2)} -> L3={len(l3)} -> L4={len(l4)} -> L5={len(l5)}")

    # L5 audit: report what L5 excluded and why
    l5_excluded = sorted(l4 - l5)
    if l5_excluded:
        from collections import defaultdict
        by_mode = defaultdict(list)
        for g in l5_excluded:
            by_mode[L5_EXPERT_EXCLUSIONS[g]].append(g)
        print("L5 exclusions by mode:")
        for mode, genes in sorted(by_mode.items()):
            print(f"  {mode:<26}: {', '.join(genes)}")

    admissible = l5

    # Single-gene trace mode
    if args.gene:
        g = args.gene
        print(f"\n=== Cascade trace for {g} (indication={args.indication}) ===")
        for layer, name, fn in [(1, "modality (basic)", lambda g, d: L1(g, d)),
                                  (2, "disease evidence", lambda g, d: L2(g, d, scope)),
                                  (3, "druggability", lambda g, d: L3(g, d)),
                                  (4, "safety audit", lambda g, d: L4(g, d)),
                                  (5, "expert deliverability", lambda g, d: L5(g, d))]:
            ok = fn(g, db)
            note = ""
            if layer == 5 and not ok:
                note = f"  [{L5_EXPERT_EXCLUSIONS[g]}]"
            print(f"  L{layer} {name:<24}: {'✓ PASS' if ok else '✗ FAIL'}{note}")
        if g in admissible:
            opp, ev, ph, ot_s, gw, pm = L6_opportunity(g, db, scope)
            scored = sorted(admissible, key=lambda x: -L6_opportunity(x, db, scope)[0])
            rank_full = scored.index(g) + 1
            print(f"  L6 opportunity rank = #{rank_full} of {len(admissible)} ({args.indication}-scoped)")
            pm_label = f"PubMed_metabolic={pm}" if scope['use_pubmed'] else "PubMed=n/a"
            print(f"     score={opp:.3f}  OT_sum={ot_s:.3f} GWAS={gw} {pm_label} max_phase={ph}")
        return 0

    # L6 ranking output
    scored = [(g, *L6_opportunity(g, db, scope)) for g in admissible]
    scored.sort(key=lambda x: -x[1])

    print(f"\n{'='*100}")
    print(f"L6 RANKING — top 30 of {len(admissible)} cascade-admissible ({args.indication}-scoped, by opportunity index)")
    print(f"{'='*100}")
    print(f"{'#':<4} {'Gene':<12} {'Opp':>6} {'Evid':>5} {'Ph':>3} {'OTsum':>5} {'GWAS':>5} {'PubMed':>6} {'Class':<25}")
    for i, (g, opp, ev, ph, ot_s, gw, pm) in enumerate(scored[:30], 1):
        pc = db['uniprot'].get(g, {}).get('protein_class', '?')
        pm_str = f"{pm:>6}" if scope['use_pubmed'] else f"{'n/a':>6}"
        print(f"{i:<4} {g:<12} {opp:>6.2f} {ev:>5.2f} {ph:>3} {ot_s:>5.2f} {gw:>5} {pm_str} {pc:<25}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
