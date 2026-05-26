# AI Discovery Pipeline

A two-phase autonomous loop for designing and running a methodologically pre-registered
AI discovery pipeline that ranks protein targets for the obesity + type 2 diabetes +
metabolic-associated steatohepatitis (MASH) indication.

## Architecture

- **Phase α** (evaluator-free methodology design)
- **Methodology lock** via `git tag v1.0-methodology-locked` + `pipeline/LOCKED_ARTIFACTS.json`
- **Phase β** (post-lock engineering iteration with verbose External Evaluator)

See `../draft.md` and `../plan.md` (in repository root) for full specification.

## Single-Command Run

```bash
./pipeline/run_pipeline.sh <input_json> <output_json> <round_number>
```

Produces:
- `<output_json>` matching the AC-2 output schema
- `runs/round_N/reviewer_ensemble_verdict.json`
- `runs/round_N/reviewer_backbone_assignment.json`
- `runs/round_N/platform_compatibility_top25.tsv`

## Components

| Path | Purpose |
|------|---------|
| `universe/build_universe.py` | Deterministic, target-agnostic candidate universe construction |
| `scoring/dimensions.json` + `weights.json` | Locked scoring schema |
| `scoring/score_*.py` | Per-dimension scorers |
| `reviewers/R[1-6]_*.md` + `run_ensemble.sh` | Six-persona Cell-reviewer ensemble (Inner Pipeline component) |
| `anti_bias/run_suite.sh` | LOO ablation + negative controls + literature-blinded re-rank + cross-biobank MR (OPTIONAL) + permutation test |
| `post_hoc/platform_compatibility.py` | saRNA + sublingual microneedle delivery feasibility check |
| `assemble_output.py` | Compose final output JSON per AC-2 contract |
| `data_sources/snapshots/` | Cached public data (Open Targets, GWAS Catalog, ChEMBL, literature, UniProt) |

## Reproducibility

`./scripts/canonicalize_output.py` strips runtime-dependent fields for byte-identical comparison.

## Provenance and Audit

- `scripts/scan_target_leakage.sh` — verify Pipeline source contains no forbidden gene identifiers
- `scripts/verify_methodology_lock.sh` — verify locked artifacts match SHA256 manifest
- `scripts/preflight.sh` — environment / cache / credential check before loop start
