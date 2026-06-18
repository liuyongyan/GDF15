# GDF15 — saRNA-deliverable obesity target selection

This repository documents how the Cheng Lab arrived at **GDF15** as the wet-lab
validation target for the saRNA + sublingual-microneedle delivery platform,
starting from a constraint-driven shortlist over all ~20k human protein-coding
genes.

The work here is a **honest reckoning**: GDF15 is *not* the single
objectively-top-ranked target produced by the data cascade. It is one of
~112 cascade-admissible obesity-scoped candidates, ranked #10 by
obesity-scoped opportunity score (top decile). The case for picking GDF15
first rests on three **cascade-external derisking signals** — a natural
human knockout experiment (hyperemesis gravidarum), a fully characterized
receptor (GFRAL), and an active Phase-1 industry asset (NGM120). See
`TARGET_SELECTION_RATIONALE.md` for the full non-expert narrative.

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
python3 cascade.py                                 # default: --indication metabolic
python3 cascade.py --indication obesity            # obesity-scoped (this paper)
python3 cascade.py --indication obesity --gene GDF15   # single-gene trace
python3 cascade.py --indication t2d                # T2D shortlist
python3 cascade.py --indication mash               # MASH shortlist
```

Expected cascade chain by indication scope (with current snapshots).
L1-L5 are boolean gates (filter); L6 is the opportunity ranker applied
to the L5 admissible set.

| Indication | L1 | L2 | L3 | L4 | L5 | GDF15 L6 rank |
|---|---|---|---|---|---|---|
| `metabolic` (broadest) | 1921 | 852 | 239 | 239 | 219 | #26 of 219 |
| `obesity` (this paper) | 1921 | 426 | 128 | 128 | **112** | **#10 of 112** |
| `t2d` | 1921 | 460 | 139 | 139 | 121 | — |
| `mash` | 1921 | 277 | 93 | 93 | 83 | — |

The six layers in execution order:

| Layer | Role | What it does |
|---|---|---|
| L1 | gate | Modality compatibility (secreted + ORF size) |
| L2 | gate | Disease evidence (indication-parameterized) |
| L3 | gate | Druggability (5 signaling secreted-protein classes only) |
| L4 | gate | Historical safety audit (vacuous for this modality — itself a finding) |
| L5 | gate | Expert deliverability curation (4 saRNA-specific failure modes: short half-life, prohormone processing, obligate heterodimer, UniProt misclassification) |
| L6 | rank | Opportunity index = evidence / (1 + max_clinical_phase), indication-scoped |

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
