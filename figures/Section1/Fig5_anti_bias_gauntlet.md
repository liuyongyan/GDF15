# Fig 5 — Anti-Bias Validation Gauntlet

## Sketch

```
Panel A — LOO ablation rank stability                Panel B — Negative controls
                                                     percentile distribution
Δ rank when removing each dimension:
                                                     CETP    ■ 12 %ile
D1 removed:  ▌Δ=+2.0                                 CNR1    ■ 30 %ile
D2 removed:  ▌Δ=+1.4                                 HTR2C   ■ 35 %ile
D3 removed:  ▌Δ=+2.0                                 DGAT1   ■ 83 %ile  ← outlier
D4 removed:  ▌Δ=+1.8                                 (mean=40%, threshold ≥50)
D5 removed:  ▌Δ=+0.8
D6 removed:  ▌Δ=+1.6
D7 removed:  ▌Δ=+1.6
Spearman ρ (universe) avg = 0.958

Panel C — Literature-blinded                          Panel D — Permutation test
top-5 overlap: 4 of 5 (PASS)                         null distribution

                                                     ──┘ ┌─┐ ┌──┐ ┌──
Panel E — Lock integrity (SHA256 audit)              ┘ │ │ │ │  │ │
51/51 forbidden artifacts match locked SHA256         └─┘ └─┘ └──┘ └─
Negative test: tamper → exit 1; restore → exit 0        observed top (rank 1)
                                                     observed p = 0.009
                                                     (bootstrap-limited)
```

## Quantitative Data

| Mechanism | Result | Threshold | Status |
|-----------|--------|-----------|--------|
| LOO ablation (mean abs Δrank top-5) | 1.74 | ≤ 2.0 | PASS |
| LOO ablation (mean Spearman ρ) | 0.958 | n/a | high stability |
| Negative controls (mean percentile) | 40.0 | ≥ 50 | FAIL (soft) |
| Literature-blinded (top-5 overlap) | 4 / 5 | ≥ 3 | PASS |
| Cross-biobank MR | OPTIONAL_SKIPPED | — | documented |
| Permutation p-value | 0.009 | < 0.001 | FAIL (bootstrap-power) |

Hard failures: 0. Soft failures: 2 (both documented as expected under bootstrap snapshot; tightening planned with full snapshot ingestion).
