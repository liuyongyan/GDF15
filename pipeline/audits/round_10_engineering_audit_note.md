# Engineering Audit Note — Round 10 (2026-05-27)

## Purpose
Document mutations to LOCKED forbidden-mutability artifacts during Round 10 close-out.
Round 10 fixes three correctness bugs Codex R9 found in Round 9's "completed" work:
(a) the normalizer dropped real blockers because it assumed one rigid schema; (b) the
validator did count-only enforcement; (c) the evaluator resolved embedded
`anti_bias_artifact_paths` against the wrong directory and produced UNKNOWN diagnostics.

## Forbidden-mutability artifacts changed (3)

### 1. `pipeline/reviewers/blocker_normalization.py`
- **AC ref**: AC-5 (schema-robust blocker propagation)
- **Change**: Extended to handle the three schemas the six personas actually emit:
  - dict with `severity="blocker"` + text in any of: `summary`, `critique`, `assessment`,
    `detail`, `text`, `description`, `recommendation` (first non-placeholder wins);
  - dict with `blocker=true` (or `True`/`"true"`/`"yes"`) flag, text from same fields;
  - string critiques treated as blockers IFF the persona's parsed `blockers_count > 0`
    AND `len(string_critiques) == blockers_count` (otherwise too ambiguous, skip).
  Added `summary_hash` field for identity comparison and `identity_set` helper used by
  the validator.
- **Why**: Codex R9 Finding 1: current verdict had real blockers under non-`summary` keys
  (R3 `critique`, R4 `assessment`) and as bare strings (R6) that the R9 normalizer
  silently dropped. Round 10 makes normalization match the schemas in the wild without
  loosening placeholder rejection.
- **Target-blind**: yes (no target-specific logic).

### 2. `pipeline/reviewers/validate_ensemble_output.py`
- **AC ref**: AC-5 (identity-level propagation check)
- **Change**: Both deferred and regular modes now compare the
  `{(persona, summary_hash)}` set derived from `normalize_blockers(per_persona)` against
  the same set derived from `blockers_remaining`. Validator fails when any real blocker
  is missing from the propagated list (not just when counts mismatch).
- **Why**: Codex R9 Finding 2: count-only checks can pass with fabricated blockers
  while real ones are dropped. Identity comparison enforces "contains every real blocker".
- **Target-blind**: yes.

### 3. `evaluator/evaluator.py`
- **AC ref**: AC-7 (correct same-run artifact resolution)
- **Change**: LOO and lit-blinded verifications now resolve embedded repo-root-relative
  `anti_bias_artifact_paths` against the repo root (computed from `__file__`), not
  against `Path(input_path).parent.parent`. The R9 implementation produced
  `runs/runs/round_N/anti_bias/...` and turned both target-specific checks into UNKNOWN.
- **Why**: Codex R9 Finding 3.
- **Target-blind**: yes (target-specific check uses the gitignored expected_answer.json,
  orthogonal to path resolution).

## Audit_required artifacts unchanged in R10
- `pipeline/reviewers/run_ensemble.sh`: no schema change required (still wraps
  `normalize_blockers` and writes `blockers_remaining` from the result).
- `pipeline/run_pipeline.sh`: no change.
- `pipeline/assemble_output.py`: no change; repo-root-relative paths it writes are now
  resolved correctly by the evaluator.

## Re-lock action
- After this audit note commits, `pipeline/LOCKED_ARTIFACTS.json` hashes will be
  refreshed for the 3 changed forbidden artifacts.
- The `v1.0-methodology-locked` tag will be force-moved to the Round 10 close-out
  commit. The R9 lock at `6c9d912` is superseded.

## Evidence regenerated post-R10 code fixes
- `runs/round_8/output.json`: `pre_registration_hash` now equals the current tag SHA.
  Reviewer evidence is honest (`overall_status=BLOCKERS_PRESENT` with 1 real blocker
  identity-propagated; all six personas invoked LIVE this run, no cache hits).
- `diagnostics/round_8.md`: LOO target-specific check shows PASS (was UNKNOWN);
  lit-blinded target-specific check shows PASS (was UNKNOWN).
