# Cell Section 1 Figures (AC-12)

Publication-grade figures for Section 1 of the Cell manuscript, generated from
`runs/round_N/` artifacts by `figures/Section1/generate_figures.R`.

## Output

`figures/Section1/output/` contains seven figures, each as **PNG at 300 dpi** and
**PDF** (vector):

| File | Content | Primary data source |
|------|---------|---------------------|
| `Fig1_architecture.png` / `.pdf` | Target-blind pipeline architecture overview (Steps 1–7 surfaced) | hard-coded layout (architecture is intrinsic) |
| `Fig2_candidate_universe.png` / `.pdf` | Universe → emitted top-N → reviewed top-25 funnel | `runs/round_N/output.json` (`ranked_targets_full_count`, `ranked_targets`) |
| `Fig3_per_dim_heatmap.png` / `.pdf` | Per-dimension z-scores for the anonymized top-25 | `runs/round_N/output.json.ranked_targets[].per_dimension_scores` |
| `Fig4_composite_ranking.png` / `.pdf` | Composite z-score bar chart for the anonymized top-25 | `runs/round_N/output.json.ranked_targets[].composite_score` |
| `Fig5_anti_bias_gauntlet.png` / `.pdf` | Per-mechanism PASS / FAIL / SKIPPED panel + actual vs threshold | `runs/round_N/anti_bias/_validation_summary.json` |
| `Fig6_reviewer_ensemble.png` / `.pdf` | Per-persona blocker counts + backbone-used + propagated/adjudicated counts | `runs/round_N/reviewer_ensemble_verdict.json` (run-local; reads `verdict.meta_review.adjudications` only — no sidecar) |
| `Fig7_post_hoc_platform.png` / `.pdf` | Post-hoc platform compatibility status distribution | `runs/round_N/platform_compatibility_top25.tsv` |

## How to regenerate

```bash
# Default: pick the latest numeric runs/round_N/
Rscript figures/Section1/generate_figures.R

# Pick a specific round
Rscript figures/Section1/generate_figures.R --round 8
```

The script writes both PNG and PDF for every figure that has the required artifacts.
If a required artifact is missing for one figure, the script SKIPS that figure with a
clear stderr warning naming the artifact and the figure — it does NOT produce a
misleading placeholder.

## R dependencies

| Package | Min version (tested) | Purpose |
|---------|-----------------------|---------|
| `ggplot2` | 3.5.0 | core grammar of graphics |
| `scales` | 1.3.0 | axis label formatting (`comma`, etc.) |
| `cowplot` | 1.1.3 | (panel assembly support, optional but linked) |
| `jsonlite` | 1.8.8 | reading `output.json`, `verdict.json`, `_validation_summary.json` |
| `dplyr` | 1.1.4 | tabular manipulation |
| `tidyr` | 1.3.1 | tabular reshape |

The script checks all six packages at startup and exits non-zero with
`missing-package: <pkg>` on stderr if any is unavailable, before producing any
output.

## Why R (not Python / matplotlib)?

Cell figure typography and color discipline are most easily met with the
ggplot2 / cowplot defaults. Per AC-12 the figures must be **publication-grade**,
not sketches; ggplot2 + the PDF device gives true vector output suitable for
direct typesetting into a Cell manuscript without rasterization loss.

## Target-blindness

The R script reads candidate IDs only from runtime artifacts. Figures 3, 4, 5, 6, 7
use the **anonymized candidate IDs** (`candidate_NNN`) the reviewer dossier uses,
not gene symbols. Figure 2 reports only sizes (no names). Figure 1 is layout-only
and has no candidate references. This keeps the figures consistent with the
target-blind reviewer dossier (AC-5) and the source-leakage scan (AC-2).
