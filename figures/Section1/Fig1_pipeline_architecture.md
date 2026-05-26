# Fig 1 — Pipeline Architecture Overview

## Sketch

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AI DISCOVERY PIPELINE — TWO-PHASE LOOP                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHASE α — Methodology Design (EVALUATOR-FREE)                              │
│    ┌───────────────────────────────────────────────────────────────────┐    │
│    │ Inner Pipeline                                                    │    │
│    │   universe builder ──► 8 scoring dimensions (7 ranking + 1 excl.) │    │
│    │   ──► 6-persona reviewer ensemble (random backbone per round)     │    │
│    │   ──► 5 anti-bias mechanisms (LOO, NC, lit-blind, MR, perm)       │    │
│    │   ──► assemble output JSON                                        │    │
│    └───────────────────────────────────────────────────────────────────┘    │
│       Codex methodology critique each round (NO evaluator access)           │
│       Convergence: 0 REQUIRED_CHANGES + reviewer ensemble OK + scans pass    │
│                                                                             │
│   ↓↓↓  METHODOLOGY LOCK (git tag v1.0-methodology-locked + LOCKED_ARTIFACTS) │
│                                                                             │
│  PHASE β — Engineering Iteration (VERBOSE EVALUATOR)                        │
│    ┌───────────────────────────────────────────────────────────────────┐    │
│    │ External Evaluator (lock-gated)                                   │    │
│    │   evaluator/expected_answer.json  ──► target rank, per-dim,       │    │
│    │   evaluator/expected_thresholds   ──► target-specific anti-bias   │    │
│    └───────────────────────────────────────────────────────────────────┘    │
│       Only audit_required artifacts may change, with engineering_audit_note │
│       Codex per-round forbidden-change audit via SHA256 manifest            │
│                                                                             │
│  OUTPUT: FINAL_RESULT.md + METHODOLOGY_TRANSPARENCY.md + 7 figures          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Panels

- **Panel A**: Two-phase architecture timeline (Phase α → lock → Phase β).
- **Panel B**: Locked-artifact mutability tree (forbidden vs audit_required across pipeline/, evaluator/, scripts/).
- **Panel C**: Round lifecycle diagram (proposal → implement → run → evaluate → review → decide → commit, with rate-limit and rollback branches).

## Quantitative Data

- Locked artifacts: **51** total (38 forbidden + 13 audit_required), SHA256-pinned
- Lock tag: `v1.0-methodology-locked` at commit `08e02d137b038eba677a0665605b58674dc1bc5b`
- Round count to lock: 1 (Round 1)
- Round count post-lock: 1 (Round 2)
- Lock verifier: PASS positive + FAIL negative (tamper test)
