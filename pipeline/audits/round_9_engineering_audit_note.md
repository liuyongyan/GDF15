# Engineering Audit Note — Round 9 (2026-05-27)

## Purpose
Document mutations to LOCKED forbidden-mutability and audit_required artifacts during
Round 9 close-out. All changes are target-blind and address Codex R8 review findings
(AC-5 honest blocker propagation; AC-7 run-local artifact binding; AC-9 doc sync; AC-2
same-run reviewer evidence; AC-10 honest reporting).

## Forbidden-mutability artifacts changed (4)

### 1. `pipeline/reviewers/validate_ensemble_output.py`
- **AC ref**: AC-5 (honest blocker propagation in both modes; per-persona provenance)
- **Change**:
  - REQUIRED_PER_PERSONA_FIELDS_REAL now requires `status`, `backbone_used`,
    `prompt_hash`, `input_hash` provenance.
  - Both regular and deferred modes call shared `blocker_normalization.normalize_blockers`
    and reject verdicts where `len(blockers_remaining)` is less than the normalized count.
  - Regular mode now requires all six personas present.
  - Reviewer self-contradictions (`blockers_count > 0` with no real critique surviving
    normalization) surface as WARN (not error).
- **Why**: Codex R8 demanded both modes apply the same propagation invariant, that
  per-persona provenance be recorded for audit, and that the normalization recognize
  case-insensitive severity + string critiques + reject placeholder summaries.
- **Target-blind**: yes.

### 2. `evaluator/evaluator.py`
- **AC ref**: AC-7 (refuse stale scratch artifact paths)
- **Change**: LOO and lit-blinded verifications now resolve `anti_bias_artifact_paths.*`
  relative to the output's repo root; refuse to read from `pipeline/anti_bias/` scratch
  prefix; UNKNOWN with explicit message when path is absent or stale.
- **Why**: Codex R8: evaluating an older output after a later pipeline run was reading
  the later run's artifacts. Same-run binding is now mandatory.
- **Target-blind**: yes.

### 3. `scripts/canonicalize_output.py`
- **AC ref**: AC-9 (canonical exclusion contract)
- **Change**: no functional change in this round; hash refresh only (already includes
  `anti_bias_artifact_paths` from R8).
- **Why**: lock manifest re-pin to current state.

### 4. `pipeline/reviewers/redact_forbidden.py`
- **AC ref**: AC-5
- **Change**: no functional change in this round; hash refresh only.

## New artifacts (added to LOCKED_ARTIFACTS.json)

- `pipeline/reviewers/blocker_normalization.py` (mutability=forbidden) — shared blocker
  normalization routine used by both verdict-writer modes and the validator. Single source
  of truth for case-insensitive severity, string/dict critique handling, and
  placeholder-summary filtering.

## Audit_required artifacts changed (4)

### 5. `pipeline/reviewers/run_ensemble.sh`
- Both regular and deferred verdict assemblers now import and call
  `blocker_normalization.normalize_blockers`; emit per-persona provenance via
  `_provenance.tsv`; overall_status derived from the normalized count, not the raw parsed
  count (so placeholder blockers don't trigger BLOCKERS_PRESENT).

### 6. `pipeline/reviewers/build_reviewer_dossier.py`
- Rewritten to build the dossier directly from same-run `candidate_universe.tsv`,
  `_scores_*.tsv`, `weights.json`, and `_validation_summary.json`. Removed
  `--source-output` and all prior-output mtime selection.

### 7. `pipeline/run_pipeline.sh`
- Step 5b (new): copies `_results_*.json` and `_validation_summary.json` from
  `pipeline/anti_bias/` to `runs/round_N/anti_bias/` BEFORE Step 6 reviewer ensemble.
- Step 6: no more `--source-output` prior selection; dossier built strictly from current run.

### 8. `pipeline/assemble_output.py`
- `anti_bias_artifact_paths` now resolved against `runs/round_N/anti_bias/` (run-local)
  and stored as repo-root-relative when possible; only falls back to scratch absolute when
  the run-local copy is genuinely absent.

## Re-lock action
- `v1.0-methodology-locked` will be moved forcibly to the Round 9 commit AFTER all R9
  fixes land. This supersedes the earlier R8 attempted re-lock (which the Round 8 audit
  note had said "will be" moved but never was). FINAL_RESULT.md will reference the R9
  commit, not the R8 commit.
- LOCKED_ARTIFACTS.json: hashes refreshed for the 8 changed artifacts; +1 new artifact
  (`blocker_normalization.py`) added. Total: 53 artifacts.

## Honest deltas vs. Round 8 plan
- AC-8 lifecycle hooks: NOT addressed in R9 (out-of-scope per round-9-contract.md;
  stays PARTIAL).
- AC-9 clean-clone replay: NOT addressed in R9 (out-of-scope; stays PARTIAL with explicit
  acknowledgement in `pipeline/CANONICAL_EXCLUSIONS.md`).
