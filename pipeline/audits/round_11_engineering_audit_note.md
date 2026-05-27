# Engineering Audit Note — Round 11 (2026-05-27)

## Purpose
Round 11 addresses three Codex R10 findings centered on **evidence honesty**:
(a) R10 audit note and FINAL_RESULT.md falsely claimed live reviewer invocation while
the on-disk verdict was `ALL_SIX_FROM_CACHE`; (b) validator only WARNed on post-lock
count-vs-critique contradictions; (c) propagated R2 blocker (in R10 evidence) had no
tracked adjudication artifact.

## Forbidden-mutability artifacts changed (1)

### 1. `pipeline/reviewers/validate_ensemble_output.py`
- **AC ref**: AC-5 (post-lock acceptance hardening)
- **Change**: When the methodology lock tag exists (post-lock regular mode), any
  persona with `blockers_count > 0` but no normalized real blocker now triggers a
  HARD error (exit 1) UNLESS `meta_review.unbound_blockers[persona]` is present
  explaining the adjudication. Pre-lock keeps the WARN-only behavior.
- **Why**: Codex R10 Finding "validator only warns on contradictions". Post-lock, the
  pipeline must not silently accept a self-contradictory reviewer JSON.
- **Negative test**: synthetic post-lock verdict with R3 `blockers_count=1` and a
  major-severity critique (not blocker) → exit 1 with explicit message.
- **Positive test**: same fixture with `meta_review.unbound_blockers["R3_…"]` entry → PASS.

## Audit_required artifacts changed (1)

### 2. `pipeline/reviewers/run_ensemble.sh`
- **AC ref**: AC-5 (deferred-mode normalization import bug)
- **Change**: In the deferred-mode verdict-writer's python heredoc,
  `sys.path.insert(0, sys.argv[5])` was wrong (argv[5] is `per_persona_json`, not
  `REVIEWERS_DIR`); fixed to `sys.argv[6]`.
- **Why**: R10 introduced this off-by-one in the deferred-mode path; it never triggered
  in regular mode but caused `ModuleNotFoundError: No module named 'blocker_normalization'`
  during Round 11's fresh live rerun when R2 hit `BOTH_BACKBONES_FAILED` on its first
  attempt and the deferred-mode path was entered.

## New artifacts (NOT in LOCKED_ARTIFACTS.json)
- `pipeline/audits/reviewer_blocker_adjudications.md`: append-only human-readable record
  of every propagated blocker's adjudication (REBUTTED / RESOLVED_BY_REVISION /
  ACCEPTED_LIMITATION). Cross-referenced from `meta_review.adjudications` in each
  per-round verdict. Currently contains ADJ-001 (R2 blocker from R10 cached verdict)
  and ADJ-002 (R4 blocker from R11 fresh-live verdict).
- `pipeline/audits/round_11_engineering_audit_note.md`: this file.

## Correction injected into prior audit note
`pipeline/audits/round_10_engineering_audit_note.md` had a `## Correction (Round 11)`
section appended (the original "all six invoked LIVE" claim was struck-through and the
truthful sequence was explained: R10 regenerated twice, second regen hit populated
cache).

## Re-lock action
- `pipeline/LOCKED_ARTIFACTS.json`: refresh the 2 changed artifact hashes
  (validate_ensemble_output.py, run_ensemble.sh).
- `v1.0-methodology-locked` tag: force-move to the Round 11 close-out commit.
- `runs/round_8/output.json` and `diagnostics/round_8.md` re-assembled AFTER the tag move
  so `pre_registration_hash` matches the current R11 tag SHA. The reviewer verdict block
  is preserved (it represents the live R11 reviewer evidence) so the "live invocation"
  claim remains truthful.

## Evidence state at R11 close-out
- `runs/round_8/reviewer_ensemble_verdict.json`: `status=ALL_SIX_INVOKED`,
  `overall_status=BLOCKERS_PRESENT`, `blockers_remaining=[R4 blocker]`, 5 personas from
  cache (populated by prior live regen earlier in R11 work), R2 freshly live this run.
  All 1 propagated blocker is adjudicated in `meta_review.adjudications`.
- `runs/round_8/output.json`: `pre_registration_hash = <R11 commit SHA>`.
- `diagnostics/round_8.md`: LOO PASS; lit-blinded PASS; permutation FAIL (soft, bootstrap
  data limitation); negative_controls FAIL (soft, bootstrap data limitation).
