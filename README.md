# GDF15 — saRNA-deliverable obesity target selection

This repository documents how the Cheng Lab arrived at **GDF15** as the wet-lab
validation target for the saRNA + sublingual-microneedle delivery platform,
starting from a constraint-driven shortlist over all ~20k human protein-coding
genes.

The work here is a **honest reckoning**: GDF15 is *not* the single
objectively-top-ranked target produced by the data cascade. It is one of
~219 cascade-admissible candidates (rank #26 overall, #18 in the obesity
subset). The case for picking GDF15 first rests on three **cascade-external
derisking signals** — a natural human knockout experiment (hyperemesis
gravidarum), a fully characterized receptor (GFRAL), and an active Phase-1
industry asset (NGM120). See `TARGET_SELECTION_RATIONALE.md` for the
full non-expert narrative.

## Repository layout

```
TARGET_SELECTION_RATIONALE.md   Main deliverable — narrative + cascade results
cascade.py                       5-layer constraint cascade implementation
data/
  snapshots_real/                ETL'd target-evidence snapshots (committed)
    opentargets_metabolic_associations.tsv   (Open Targets v26.03)
    gwas_catalog_metabolic_loci.tsv          (NHGRI-EBI GWAS Catalog)
    uniprot_protein_classes.tsv              (UniProt SwissProt human reviewed)
    literature_metabolic_genes.tsv           (PubMed via NCBI E-utilities)
    ETL_LOG.md                               (provenance + row counts)
  raw_dumps/                     Original public-DB dumps (~1.5 GB, gitignored)
  etl/                           ETL scripts that produced snapshots_real/
references/                      Cited PDFs (gitignored; kept locally)
```

## Reproducing the cascade

```bash
python3 cascade.py                # full top-30 + obesity-only top-30
python3 cascade.py --gene GDF15   # single-gene trace with rank
```

Expected output (with current snapshots):

```
Cascade: 19327 -> L1=1921 -> L2=852 -> L3=239 -> L5=239 -> L6=219
Obesity-specific subset: 112
```

The six layers are: L1 modality compatibility, L2 disease evidence,
L3 druggability (signaling classes only), L4 opportunity index (ranking,
not filter), L5 historical safety audit (vacuous for our modality —
itself a finding), L6 expert deliverability curation (catches short
half-life, prohormone processing, obligate heterodimer, and UniProt
misclassification — failure modes not captured by L1's coarse structural
check).

## What is not in this repo

Earlier exploratory infrastructure (an 8-dimension scoring pipeline, a
6-persona reviewer ensemble, anti-bias gauntlet, Cell-paper figures, and the
humanize/RLCR loop scaffolding) lived under `pipeline/`, `evaluator/`,
`figures/`, and `scripts/` in prior commits. Those approaches were superseded
by the simpler 5-layer cascade documented here; the artifacts remain
recoverable from git history (`git log --all --oneline`) if ever needed.

## Provenance

- Open Targets v26.03 (March 2026 release)
- GWAS Catalog full dump, retrieved 2026-06
- UniProt SwissProt human reviewed, release 2026_03
- ChEMBL via REST API, queried by MeSH indication ID (8 metabolic indications)
- PubMed via NCBI E-utilities (rate-limited, 1918 genes, API key required for ETL re-run)
