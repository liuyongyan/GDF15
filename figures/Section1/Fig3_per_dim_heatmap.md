# Fig 3 — Per-Dimension Scoring Heatmap

## Sketch

```
                                D1   D2   D3   D4   D5   D6   D7   D8*
GDF15            ─►    ████ ████ ████ ████ ████ ████ ████ ████   z=+1.68 (rank 1)
LEP              ─►    ████ ███  ████ ████ ████ ███  ████ ████   z=+1.67 (rank 2)
ANGPTL3          ─►    ███  ████ ████ ███  ████ ████ ████ ████   z=+1.61 (rank 3)
APOB             ─►    ███  ███  ████ ████ ████ ███  ███  ████   z=+1.45 (rank 4)
FGF21            ─►    ███  ███  ████ ████ ████ ████ ███  ████   z=+1.44 (rank 5)
... (696 candidates total)

* D8 = platform_deliverability (excluded from composite)
```

Color scale: blue = low z-score; white = z≈0; red = high z-score (clamped to [-3, +3]).

## Panels

- **Panel A**: Full heatmap (696 candidates × 8 dimensions). Expected-target row highlighted at top.
- **Panel B**: Violin per dimension showing distribution of z-scores across the universe; expected target marked.
- **Panel C**: Rank-rank scatter for each dimension pair (28 sub-panels in supplementary); expected target consistently top-quartile.

## Quantitative Data

- Total candidates × dimensions = 696 × 8 = 5,568 cells.
- Missingness: ~20–60% depending on dimension (zero-filled with missingness flag).
- Expected target dimension scores: D1=+1.98, D2=+1.24, D3=+1.92, D4=+2.01, D5=+1.46, D6=+1.19, D7=+1.95, D8=+1.41.
- Weighted composite at expected target: +1.678.
- Composite distribution across 696 candidates: mean ~0.0 (z-scored), max +1.678, min -1.85.
