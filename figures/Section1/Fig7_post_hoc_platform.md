# Fig 7 — Post-Hoc Platform Compatibility Check

## Sketch

```
Top-25 candidates × platform criteria PASS/FAIL grid:

Rank Gene          Secreted ORF≤15kb SignalPep Overall
─────────────────────────────────────────────────────
  1  GDF15           PASS    PASS     PASS     PASS ★ ← uniquely top-ranked AND fully platform-compatible
  2  LEP             PASS    PASS     PASS     PASS
  3  ANGPTL3         PASS    PASS     PASS     PASS
  4  APOB            PASS    PASS     PASS     PASS (ORF=13.7kb, near upper limit)
  5  FGF21           PASS    PASS     PASS     PASS
  6  (augmented)     PASS    PASS     PASS     PASS
  7  PCSK9           PASS    PASS     PASS     PASS
  8  APOC3           PASS    PASS     PASS     PASS
  9  ADIPOQ          PASS    PASS     PASS     PASS
 10  ANGPTL4         PASS    PASS     PASS     PASS
 ...

GDF15 mechanism cartoon:
  ┌────────────────────────────────────────────────────────────┐
  │   sublingual microneedle patch                              │
  │      ↓ saRNA payload (encoded protein in mucosal cells)     │
  │   oral mucosa "factory"                                     │
  │      ↓ secreted protein                                     │
  │   systemic circulation                                      │
  │      ↓                                                      │
  │   hindbrain GFRAL receptor (target receptor restricted to   │
  │      area postrema and NTS → narrow, safe activation site)  │
  │      ↓                                                      │
  │   metabolic effects: fat-mass ↓, lean-mass →, glucose ↑,    │
  │      hepatic steatosis ↓, durability via continuous local   │
  │      saRNA-driven production                                │
  └────────────────────────────────────────────────────────────┘

```

## Panels

- **Panel A**: Top-25 × platform criteria PASS/FAIL grid.
- **Panel B**: Expected-target-specific mechanism cartoon (saRNA + sublingual microneedle → mucosal expression → secreted protein → hindbrain receptor → multi-axis metabolic effect).
- **Panel C**: Bridges to Section 2 — "this prediction was validated experimentally in three mouse models of MASH-associated obesity."

## Quantitative Data

- Top-10 candidates passing all platform criteria: **10 of 10** (broad universe of secreted, properly-sized protein candidates).
- Expected target: rank 1; PASS on all 4 platform criteria (secreted, ORF in window, signal peptide, active from circulation).
- Expected target ORF: 915 bp (well within saRNA payload limit of ~15 kb).
- Platform-compatibility-aware ranking: 10/10 in top 10 deliverable; the post-hoc check confirms broad amenability and identifies the expected target as the highest-ranked deliverable candidate.
