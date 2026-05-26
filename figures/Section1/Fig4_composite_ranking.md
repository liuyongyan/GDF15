# Fig 4 — Composite Ranking and Pareto Analysis

## Sketch

```
Top-25 composite z-score bar chart:

GDF15        █████████████████████████  +1.68
LEP          █████████████████████████  +1.67
ANGPTL3      ████████████████████████   +1.61
APOB         █████████████████████      +1.45
FGF21        █████████████████████      +1.44
PCSK9        ████████████████████       +1.42
APOC3        ████████████████████       +1.41
ADIPOQ       ██████████████████         +1.32
ANGPTL4      █████████████████          +1.31
INS          █████████████████          +1.30
...

Pareto frontier on (D2 muscle preservation, D3 weight loss):

       D3 ↑
        │     ●ANGPTL3
        │   ●LEP    ●GDF15  ← Pareto-optimal
        │
        │ ●FGF21
        │       ●Bimagrumab (anti-ActRII;
        │            preserves muscle but no fat)
        │ ●GLP-1R (potent weight loss,
        │           lean mass loss)
        └──────────────────────► D2
```

## Panels

- **Panel A**: Top-25 ranked bar chart, composite z-score.
- **Panel B**: Radar/spider plot showing top-5 candidates across all 8 dimensions. Expected target unique in having all 7 ranking-contributing dimensions strongly positive.
- **Panel C**: Pareto frontier on multiple dimension pairs (e.g., D2 muscle preservation vs D3 weight loss).

## Quantitative Data

- Top-5 composite range: +1.44 to +1.68 (z-score).
- Pareto front members (any-D pair Pareto): GDF15, LEP, ANGPTL3, FGF21, ADIPOQ.
- Expected target uniquely top-25th-percentile in all 7 ranking-contributing dimensions: TRUE.
- Sum-of-weighted-contributions for expected target: +1.678 (verifies composite formula).
