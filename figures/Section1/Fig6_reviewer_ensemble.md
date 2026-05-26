# Fig 6 — Six-Persona Cell-Reviewer Ensemble

## Sketch

```
                       ┌─────────────────────────────┐
                       │  Meta-Review Aggregator     │
                       │  (consensus blockers,       │
                       │   single-reviewer blockers, │
                       │   pipeline methodology)     │
                       └──┬────┬────┬────┬────┬────┬─┘
                          │    │    │    │    │    │
                ┌─────────┘    │    │    │    │    └─────────┐
                ▼              ▼    ▼    ▼    ▼              ▼
     ┌────────────────┐   ┌─────────────┐ ┌──────────┐ ┌─────────────┐
     │ R1 Molecular   │   │ R2 Clinical │ │ R3 Stats │ │ R4 Pharm    │
     │    Biologist   │   │  Translator │ │ /Geneticist│ │/Drug Dev    │
     └────────────────┘   └─────────────┘ └──────────┘ └─────────────┘
     ┌────────────────┐   ┌─────────────┐
     │ R5 AI Methods  │   │ R6 Editor   │
     └────────────────┘   └─────────────┘

Per-round backbone assignment (deterministic random by round seed):
  round 0:  R1→codex   R2→gemini  R3→codex   R4→gemini  R5→codex   R6→gemini
  round 1:  R1→gemini  R2→codex   R3→codex   R4→codex   R5→gemini  R6→gemini
  round 2:  R1→codex   R2→codex   R3→gemini  R4→codex   R5→gemini  R6→codex

Forbidden-name redaction enforced via pipeline/reviewers/FORBIDDEN_TARGET_NAMES.txt.
Reviewer prose may never mention specific gene symbols by name; candidates are
referenced by anonymized ID until the final user-facing report.
```

## Panels

- **Panel A**: Six-persona architecture + meta-review aggregator + random backbone assignment per round.
- **Panel B**: Status across rounds (Round 0: MOCK_STUB pre-lock; Round 1: MOCK_STUB pre-lock-fix; Round 2: REVIEWER_DEFERRED post-lock; Round 3+: real LLM invocations).
- **Panel C**: Forbidden-name scanner enforcement (zero forbidden hits in reviewer outputs across all rounds).

## Quantitative Data

- Personas: **6** (R1–R6)
- Backbone diversity: **2** (codex via gpt-5.5; gemini via 3.1-pro)
- Backbone assignment: deterministic random by round seed; recorded per round in `reviewer_backbone_assignment.json`
- Round 2 status: `REVIEWER_DEFERRED` with full schema (status / reason / affected_personas / affected_backbones / remediation)
- Real LLM invocation: deferred to Round 3+ engineering (framework + REVIEWER_DEFERRED contract in place)
- Validator: rejects MOCK_STUB post-lock; accepts REVIEWER_DEFERRED with required schema; accepts real-mode with all 6 personas + meta_review
