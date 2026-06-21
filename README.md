# GDF15 — saRNA-deliverable obesity target selection

This repository documents how the Cheng Lab arrived at **GDF15** as the wet-lab
validation target for the saRNA + sublingual-microneedle delivery platform,
starting from a constraint-driven shortlist over all ~20k human protein-coding
genes.

The work here is a **honest reckoning**. The data cascade does not crown GDF15.
It narrows ~20k genes to a focused, ranked shortlist of **17** deliverable
obesity cargos, in which GDF15 ranks **#3** — behind CCK and HMGB1. The final
selection of GDF15 is then a **human-synthesis step** (§6 of the rationale),
which passes over the two higher-ranked candidates for clear reasons (CCK: native
half-life in minutes, no evidence the unmodified peptide works sustained; HMGB1:
a nuclear damage signal misannotated as a secreted ligand) and selects GDF15 on
three **cascade-external derisking signals**: a natural human knockout experiment
(hyperemesis gravidarum — direct proof the *native* protein, sustained, drives
weight loss), the GFRAL receptor characterized in 2017, and an active Phase-1
industry asset (NGM120).

Two honesty notes are kept explicit throughout: the new data-driven
**translational cargo suitability** gate (L5) is what makes the shortlist
deliverable — it removes higher-evidence but undeliverable proteins like BDNF and
NRG1 (BBB-restricted / broadly-expressed receptors); and GDF15 survives L5 only
because **Allen Mouse Brain ISH** localizes its receptor GFRAL (below bulk-RNA
detection) to the area postrema, a blood-accessible circumventricular organ.
Earlier revisions ran the deliverability judgments as a mechanical "L6 expert"
gate, which made GDF15 #1; that gate is removed because it was target-aware and,
for the half-life mode, in tension with GDF15's own (hours-scale) half-life — the
reasoning now lives openly in §6. See `TARGET_SELECTION_RATIONALE.md` for the
full non-expert narrative.

## Repository layout

```
TARGET_SELECTION_RATIONALE.md   Main deliverable — narrative + cascade results
cascade.py                       6-layer constraint cascade implementation
data/
  snapshots_real/                ETL'd target-evidence snapshots (committed)
    opentargets_metabolic_associations.tsv   (Open Targets v26.03)
    gwas_catalog_metabolic_loci.tsv          (NHGRI-EBI GWAS Catalog)
    uniprot_protein_classes.tsv              (UniProt SwissProt human reviewed)
    literature_metabolic_genes.tsv           (PubMed via NCBI E-utilities)
    chembl_withdrawn_status.tsv              (ChEMBL withdrawn_flag overlay for compounds with max_phase>=2)
    translational_cargo_suitability.tsv      (L5: OmniPath receptor + HPA tissue/secretome + Allen Mouse Brain ISH)
    ETL_LOG.md                               (provenance + row counts)
  raw_dumps/                     Original public-DB dumps (~1.5 GB, gitignored;
                                 incl. hpa/, omnipath/, allen/ for L5)
  etl/                           ETL scripts that produced snapshots_real/
                                 (incl. etl_translational_suitability.py)
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
to the L5 admissible set. The cascade ends at the ranked shortlist; the
single-cargo selection of GDF15 is a separate human-synthesis step (§6).

| Indication | L1 | L2 | L3 | L4 | L5 | GDF15 L6 rank |
|---|---|---|---|---|---|---|
| `metabolic` (broadest) | 1921 | 852 | 239 | 239 | 29 | #5 of 29 |
| `obesity` (this paper) | 1921 | 426 | 128 | 128 | **17** | **#3 of 17** |
| `t2d` | 1921 | 460 | 139 | 139 | 19 | #11 of 19 |
| `mash` | 1921 | 277 | 93 | 93 | 9 | #1 of 9 |

The six layers in execution order:

| Layer | Role | What it does |
|---|---|---|
| L1 | gate | Modality compatibility (secreted + ORF size) |
| L2 | gate | Disease evidence (indication-parameterized) |
| L3 | gate | Druggability (5 signaling secreted-protein classes only) |
| L4 | gate | Historical safety audit (vacuous for this modality — itself a finding) |
| L5 | gate | **Translational cargo suitability (DATA-DRIVEN)** — systemic-endocrine deliverability from OmniPath receptor mapping + HPA tissue/secretome + Allen Mouse Brain ISH: ligand secreted-to-blood, cognate receptor blood-accessible (peripheral or circumventricular-organ), receptor restricted. Only `area-postrema` receptors like GFRAL pass via the CVO route. |
| L6 | rank | Opportunity index = evidence / (1 + max_clinical_phase), indication-scoped |

Deliverability failure modes that public databases do not cover (short native
half-life, prohormone processing, obligate heterodimer, secretome misannotation)
are **not** a cascade gate. They are applied as qualitative criteria in the §6
human-synthesis step that picks GDF15 from the shortlist — not as a mechanical
filter. (An earlier revision ran them as a hand-curated "L6 expert" gate; it is
removed because it was target-aware and, for the half-life mode, inconsistent
with GDF15's own hours-scale half-life.)

## What is not in this repo

Earlier exploratory infrastructure (an 8-dimension scoring pipeline, a
6-persona reviewer ensemble, anti-bias gauntlet, Cell-paper figures, and the
humanize/RLCR loop scaffolding) lived under `pipeline/`, `evaluator/`,
`figures/`, and `scripts/` in prior commits. Those approaches were superseded
by the simpler constraint cascade documented here; the artifacts remain
recoverable from git history (`git log --all --oneline`) if ever needed.

## Provenance

- Open Targets v26.03 (March 2026 release)
- GWAS Catalog full dump, retrieved 2026-06
- UniProt SwissProt human reviewed, release 2026_03
- ChEMBL via REST API, queried by MeSH indication ID (8 metabolic indications)
- PubMed via NCBI E-utilities (rate-limited, 1918 genes, API key required for ETL re-run)
- Human Protein Atlas `proteinatlas.tsv` (tissue specificity + secretome location), proteinatlas.org
- OmniPath ligand-receptor interactions (REST API; aggregates Guide to PHARMACOLOGY, connectomeDB2020, CellTalkDB, etc.)
- Allen Mouse Brain Atlas ISH (api.brain-map.org; expression energy by structure, for circumventricular-organ localization of brain-restricted receptors)
