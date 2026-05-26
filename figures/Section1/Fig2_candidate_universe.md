# Fig 2 — Candidate Universe Construction

## Sketch

```
Sources                              Inclusion Rules                     Universe
─────────                            ───────────────                     ────────
Open Targets metabolic ──► R1: assoc_score ≥ 0.50 for any of           ┐
                                   {obesity, T2D, NAFLD, MASH}          │
                                                                        │
GWAS Catalog ────────────► R2: p < 5e-8 for any of {BMI, HbA1c,         │ UNION
                                  ALT, liver-fat, T2D, ...}             │  +
                                                                        │ DEDUP
ChEMBL metabolic ─────────► R3: max_phase ≥ 2 in any of {T2D,           │  ↓
                                  obesity, NAFLD, MASH, dyslipidemia, ...│
                                  muscle_wasting, heart_failure}        │  696
                                                                        │ genes
Literature curation ──────► R4: pubmed_count_metabolic ≥ 50             ┘
(rule-based: PubMed
 hit counts in
 metabolic context)
```

## Panels

- **Panel A**: UpSet plot of overlap among R1/R2/R3/R4 inclusion sets.
- **Panel B**: Stacked bar of protein-class distribution (14 classes with > 5%).
- **Panel C**: Distribution by therapeutic stage (preclinical / Phase 1 / Phase 2 / Phase 3 / approved).

## Quantitative Data

- Universe size: **696** protein-coding genes (within immutable 500–2000 AC range).
- Inclusion-rule contribution:
  - R1 (Open Targets): ~480
  - R2 (GWAS Catalog): ~265
  - R3 (ChEMBL): ~180
  - R4 (Literature): ~560
  - After dedup (union): 696
- Diversity check: PASS — 14 protein classes each contributing > 5%.
- Protein-class breakdown (top): GPCR 53, enzyme 48, transcription factor 44, ion channel 44, secreted hormone 46, secreted growth factor 43, secreted protein 43, etc.
- Deterministic SHA256 of universe TSV: pinned via `pipeline/data_sources/SNAPSHOT_HASHES.txt`.
