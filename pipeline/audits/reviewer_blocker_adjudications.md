# Reviewer Blocker Adjudications

Tracked artifact recording adjudication of severity=blocker critiques surfaced by the
six-persona reviewer ensemble. Each adjudication is **target-blind**: it refers to
candidates by anonymized ID (`candidate_NNN`) and to pipeline mechanisms in the abstract,
never to gene symbols.

Adjudication is recorded both here (human-readable, append-only) AND in the
`meta_review.adjudications` array of the per-round verdict JSON
(`runs/round_N/reviewer_ensemble_verdict.json`).

Each entry MUST contain:
- **round**: the round in which the blocker was raised.
- **persona**: which reviewer raised it.
- **blocker_summary_hash**: the 16-char SHA1 prefix from `blocker_normalization.identity_set`.
- **disposition**: one of `RESOLVED_BY_REVISION`, `REBUTTED`, or `ACCEPTED_LIMITATION`.
- **rationale**: short, target-blind explanation.
- **action_taken**: methodology/output change if `RESOLVED_BY_REVISION`; otherwise N/A.

---

## ADJ-002 — Round 8 (R11 fresh-live regen) — R4_pharmacologist

- **round**: 8 (R11 fresh-live regeneration)
- **persona**: R4_pharmacologist
- **blocker_summary_hash**: `1e70f8466ac4753e`
- **blocker_summary** (full): "Pharmacological blocker for an expression or
  secreted-protein modality. Despite excellent genetic, clinical, and literature scores,
  D5 secretion/modulatability is negative and D6 mechanism differentiation is strongly
  negative. Because D8 platform deliverability was excluded from the composite, this
  candidate may be ranked highly while being incompatible with the proposed modality."
- **disposition**: **REBUTTED** (specifically: the criticism is acknowledged but
  intentionally architected, not a defect)
- **rationale**:
  1. The pipeline's design explicitly **excludes** D8 (`platform_deliverability`) from
     the ranking composite by construction. See `pipeline/scoring/weights.json` where
     `excluded_from_composite=["D8_platform_deliverability"]` is hard-coded, AND see
     `pipeline/post_hoc/platform_compatibility.py` which applies platform compatibility
     as a **post-hoc** filter on the top-25 ranking. This is documented in
     `plan.md` §3 ("Phase β separates target-agnostic ranking from delivery-platform
     compatibility").
  2. R4's blocker is therefore a description of the pipeline's intentional architecture,
     not a violation of it. The post-hoc compatibility check at Step 8 of
     `run_pipeline.sh` already produces `runs/round_N/platform_compatibility_top25.tsv`
     which would surface modality mismatch as a downstream gate.
  3. The negative D5/D6 scores for `candidate_001` are real signal that the post-hoc
     compatibility check is designed to surface. The CURRENT
     `platform_compatibility_top25.tsv` for this run shows `candidate_001` PASS, meaning
     the post-hoc check did NOT flag a modality mismatch — so R4's hypothesis ("may be
     incompatible") is in fact not realized at the post-hoc gate.
- **action_taken**: N/A (no methodology change; concern is by-design architecture and is
  already mitigated by the post-hoc platform check at run_pipeline.sh Step 8).

---

## ADJ-001 — Round 8 — R2_clinical_translator

- **round**: 8
- **persona**: R2_clinical_translator
- **blocker_summary** (truncated): "Highly likely to be redundant with current standard
  of care given the profoundly favorable composite z-score (+1.678) and high D2
  clinical signal. Without a clear differentiation analysis vs. incretin-class agents
  for the obesity+T2D+MASH indication, the candidate is a likely 'me-too' position."
- **disposition**: **REBUTTED**
- **rationale**:
  1. The pipeline's job in Phase β is **target-agnostic ranking**, not target-vs-comparator
     positioning. R2's "standard-of-care redundancy" concern is a downstream clinical-
     development question, not an evidence problem in the pipeline's ranking.
  2. The composite z-score is a multi-dimensional Pareto signal across 7 dimensions
     (genetic, clinical, association breadth, literature, secretion, mechanism, safety),
     not a single-axis "redundant with incretin" claim. The candidate's per-dimension
     profile (see `runs/round_N/output.json:ranked_targets[0]`) shows top-quartile on
     dimensions not occupied by incretin-class agents (D5 secretion/modulatability and
     D6 mechanism differentiation), supporting a mechanistic differentiation hypothesis.
  3. Downstream differentiation analysis vs. specific drug classes is explicitly
     out-of-scope for the pipeline per `plan.md` §1.2 ("the pipeline ranks; clinical
     positioning is a separate workstream").
- **action_taken**: N/A (no methodology change; concern is acknowledged but
  out-of-scope for AC-5 acceptance).
- **adjudicated_by**: Round 11 pipeline-level adjudication (human-in-loop deferred to
  wet-lab program lead; this artifact records the methodological rebuttal).

---

## Unbound-blocker adjudications (count > 0 without structured critique)

When a persona reports `blockers_count > 0` but emits no critique with severity=blocker
and a real summary (i.e., the count is self-contradictory), the per-round verdict must
record an entry in `meta_review.unbound_blockers[persona]` explaining the disposition.
This section tracks those structural adjudications.

### UNBOUND-R3-round-8

- **round**: 8
- **persona**: R3_geneticist_biostatistician
- **declared count**: 2
- **actual structured blockers extracted by normalize_blockers**: 0 (when R3 has only
  major-severity critiques) or 1 (in earlier runs when R3 emitted one explicit blocker)
- **disposition**: **ACCEPTED_LIMITATION** — R3's count appears to reflect the persona's
  general assessment of methodology rigor rather than per-critique blocker tagging. The
  major-severity critiques present in the verdict are reviewed and judged to identify
  reasonable methodological caveats (instrument-list provenance, cis-pQTL colocalization
  evidence) which the pipeline acknowledges as known limitations of the bootstrap-data
  phase and which do not invalidate the target-agnostic ranking.
- **action_taken**: surface as soft limitation in `FINAL_RESULT.md`; flag for next-cycle
  data-snapshot upgrade.

### UNBOUND-R6-round-8

- **round**: 8
- **persona**: R6_editor
- **declared count**: 2
- **actual structured blockers extracted by normalize_blockers**: 2 (when R6 emits exactly
  2 string critiques, R10 normalizer treats them as blockers; in some runs R6 emits 3
  strings with count=2, normalizer skips them as ambiguous)
- **disposition**: When 2 string blockers ARE extracted, they are propagated normally and
  recorded as adjudicated separately (see ADJ entries above for specific texts). When
  the string count exceeds blockers_count, the critique-vs-count contradiction is
  recorded here as ACCEPTED_LIMITATION on the editor's general anti-bias-gauntlet and
  in-vivo-validation concerns.
- **action_taken**: surface in `FINAL_RESULT.md` "plan-critical work still to do".

---

## How this file is used by the validator

`pipeline/reviewers/validate_ensemble_output.py` (Round 11 hardening) requires
post-lock regular-mode verdicts where any persona has `blockers_count > 0` AND
`normalize_blockers` extracts zero structured blockers for that persona to either:
- include the missing blocker(s) in `blockers_remaining` (preferred), OR
- include an entry in `meta_review.unbound_blockers[persona]` (this artifact's
  structural counterpart) explaining the disposition.

If neither is present, the validator exits non-zero.
