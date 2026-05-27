# Engineering Audit Note — Round 8 (2026-05-27)

## Purpose
Document mutations to LOCKED forbidden-mutability and audit_required artifacts performed
during Round 8 close-out. All changes are target-blind and address blockers raised by Codex
reviewer in Rounds 6/7 (AC-5, AC-7, AC-9).

## Forbidden-mutability artifacts changed (3)

### 1. `scripts/canonicalize_output.py`
- **AC ref**: AC-9 (reproducibility canonical exclusion sync)
- **Change**: Added `"anti_bias_artifact_paths"` to `EXCLUDE_TOPLEVEL`.
- **Why**: Round 8 introduced `anti_bias_artifact_paths` (absolute paths) into the output
  to fix AC-7. These paths vary per checkout location and must be excluded from canonical
  comparison without altering scientific content.
- **Target-blind**: yes (no target-specific code path).

### 2. `pipeline/reviewers/validate_ensemble_output.py`
- **AC ref**: AC-5 (reviewer ensemble structural honesty)
- **Change**: In deferred mode, enforce per-persona parsed-field structural requirements;
  reject verdicts where `sum(blockers_count) > 0` but top-level `blockers_remaining` is empty.
- **Why**: Codex R6/R7 required honest propagation of per-persona blockers to top-level
  verdict; prior validator allowed silent zeroing.
- **Target-blind**: yes (structural check, no target-specific logic).

### 3. `evaluator/evaluator.py`
- **AC ref**: AC-7 (target-specific verification reads same-run artifacts) + AC-7 (permutation PASS/FAIL/UNKNOWN label)
- **Change**: (a) LOO and lit-blind verifications now prefer `output_json.anti_bias_artifact_paths.*`
  over the legacy scratch path under `pipeline/anti_bias/_results_*.json`. (b) Permutation
  test now emits explicit PASS/FAIL/UNKNOWN status against criterion threshold.
- **Why**: Codex R6/R7 flagged that the evaluator could silently read stale scratch files from a
  different run; this fix binds verifications to the same run's artifacts.
- **Target-blind**: yes (target identity comes from gitignored expected_answer.json — orthogonal).

## Audit_required artifacts changed (4)

### 4. `pipeline/reviewers/run_ensemble.sh`
- **AC ref**: AC-5
- **Change**: Aggregate per-persona parsed blockers into top-level `blockers_remaining`,
  emit top-level `verdict` and `overall_status`, and call `redact_forbidden.py` before any
  downstream consumer reads the verdict.

### 5. `pipeline/assemble_output.py`
- **AC ref**: AC-7
- **Change**: Emits `anti_bias_artifact_paths` (absolute) for the evaluator to derive same-run inputs.

### 6. `pipeline/run_pipeline.sh`
- **AC ref**: AC-5
- **Change**: Selects most-recent-by-mtime prior `output.json` for reviewer dossier instead of lex-last.

### 7. `scripts/loop_orchestrator.sh`
- **AC ref**: AC-8 (safer rollback)
- **Change**: Records start-of-round git ref into `runs/round_N/start_of_round_ref.txt`;
  rollback restores to that ref instead of broad `git reset --hard HEAD~1`. T_PASSES count
  derived from machine-readable JSON summary tail in diagnostic.

## New artifacts (added to LOCKED_ARTIFACTS.json)

- `pipeline/reviewers/redact_forbidden.py` (mutability=forbidden)

## Re-lock action
- New tag will be `v1.0-methodology-locked` (force-moved to R8 commit) after this audit note is committed.
- Pre-registration hashes in any prior run JSONs refer to the OLD lock commit; new runs will reference the R8 commit.
