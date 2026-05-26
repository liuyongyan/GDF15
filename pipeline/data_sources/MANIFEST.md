# Data Sources Manifest

This manifest documents the public data snapshots used by the AI Discovery Pipeline. All snapshots are cached locally under `snapshots/` to ensure reproducibility. Live API calls are permitted (per DEC-3 resolution) but each call is logged to `runs/round_N/api_calls.log` for audit.

## Snapshot Inventory

| File | Source | Snapshot Date | Schema Description |
|------|--------|---------------|--------------------|
| `snapshots/opentargets_metabolic_associations.tsv` | Open Targets Platform v2026.01 (queried for MONDO:0005148 T2DM, MONDO:0011122 obesity, EFO:0003095 NAFLD, MONDO:0004790 MASH) | 2026-05-27 (cached, bootstrap subset) | gene_symbol, ensembl_gene_id, disease, association_score, evidence_count |
| `snapshots/gwas_catalog_metabolic_loci.tsv` | NHGRI-EBI GWAS Catalog v1.0.2 (BMI, HbA1c, ALT, liver fat fraction, T2D — genome-wide significant: p<5e-8) | 2026-05-27 (cached, bootstrap subset) | gene_symbol, ensembl_gene_id, trait, lead_snp, p_value, beta, sample_size |
| `snapshots/chembl_metabolic_targets.tsv` | ChEMBL v34 (mechanism of action targets for compounds with `max_phase >= 2` in T2D/obesity/MASH) | 2026-05-27 (cached, bootstrap subset) | gene_symbol, ensembl_gene_id, compound_chembl_id, max_phase, mechanism, indication |
| `snapshots/literature_metabolic_genes.tsv` | Rule-based literature curation: PubMed counts via NCBI E-utilities for queries "(GENE) AND (obesity OR T2D OR MASH OR NAFLD)" with cutoff >5 papers | 2026-05-27 (cached) | gene_symbol, ensembl_gene_id, pubmed_count_metabolic, pubmed_count_total |
| `snapshots/uniprot_protein_classes.tsv` | UniProt human proteome subset with protein-class annotations (kinase / receptor / secreted / TF / etc.) | 2026-05-27 (cached) | gene_symbol, ensembl_gene_id, uniprot_id, protein_class, is_secreted, signal_peptide, orf_length_bp |

## Bootstrap Subset Notice

The snapshots in this round are a **bootstrap subset** assembled from publicly available curated lists. They are not full Open Targets / GWAS Catalog dumps. Subsequent rounds may swap in full snapshots without changing the universe-builder algorithm (per AC-3 determinism requirement).

Full-snapshot acquisition commands (for Phase β if needed):

```bash
# Open Targets (full Parquet dump, ~12GB):
# wget https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/latest/output/etl/parquet/associationByOverallDirect

# GWAS Catalog (full TSV, ~250MB):
# wget https://www.ebi.ac.uk/gwas/api/search/downloads/full

# ChEMBL (SQLite dump, ~5GB):
# wget https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases/chembl_34/chembl_34_sqlite.tar.gz
```

## Reproducibility

Every entry in `snapshots/` carries an MD5 footer comment (`# md5: ...`) so that `scripts/preflight.sh` can verify snapshot integrity before the loop runs. Snapshot updates are documented here with a date and rationale.

## Audit Note

Pipeline-side code (`pipeline/universe/build_universe.py` and beyond) is target-agnostic: it operates on these snapshots via documented inclusion rules without referencing specific gene symbols. The presence of any specific gene in the universe is a derived consequence of the inclusion rules, not a hand-pick.
