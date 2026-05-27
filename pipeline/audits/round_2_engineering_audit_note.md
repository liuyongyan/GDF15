# Engineering Audit Note — Round 2 (new RLCR session) — 2026-05-27

## Purpose
Round 2 closes the four immediately-actionable findings from Codex R1's review:
(a) AC-11 adjudication binding must be **run-local** inside
`reviewer_ensemble_verdict.json.meta_review.adjudications`, not a sidecar workaround
inside the walkthrough generator; (b) AC-12 missing-artifact skip must delete stale
PNG/PDF so old figures do not linger; (c) AC-10 `FINAL_RESULT.md` must be factually
consistent with current R2 artifacts (no R11 wording, no false `ALL_SIX_INVOKED`
claim, no false adjudication claim); (d) walkthrough Step 9 wording bug
(`scripts/FORBIDDEN_TARGET_NAMES.txt` is not the right reference).

## Forbidden-mutability artifacts changed (3) + audit_required (1)

### 1. `pipeline/reviewers/validate_ensemble_output.py` (forbidden)
- **AC ref**: AC-11 R2 (run-local adjudication binding enforcement)
- **Change**: After existing identity-set check, validator now calls
  `adjudication_binding.bind_adjudications` to determine which canonical
  adjudications match the verdict's propagated blockers. For each match, the
  verdict's `meta_review.adjudications` MUST contain an entry with the same
  `adjudication_id`; otherwise the validator FAILs with explicit message.
- **Why**: Codex R1 Finding 1 — the R1 walkthrough merged from sidecar JSON, making
  the run-local verdict non-compliant.

### 2. `pipeline/generate_round_walkthrough.py` (forbidden)
- **AC ref**: AC-11 R2 (prefer verdict-resident adjudications) + walkthrough wording
- **Change**:
  - Adjudication merge now reads `verdict.meta_review.adjudications` FIRST (primary,
    run-local) and falls back to canonical JSON only for entries the verdict does
    not contain.
  - Step 6 also surfaces `meta_review.unbound_blockers` when present (so R3-type
    count-vs-critique contradictions are honestly visible to the human reader).
  - Step 9 wording corrected: no longer claims `scripts/FORBIDDEN_TARGET_NAMES.txt`
    exists (it doesn't; patterns are embedded in `scan_target_leakage.sh`). Now
    references the related allowlist at `pipeline/reviewers/FORBIDDEN_TARGET_NAMES.txt`.

### 3. `pipeline/reviewers/blocker_normalization.py` — unchanged in R2.

### 4. `pipeline/reviewers/run_ensemble.sh` (audit_required)
- **AC ref**: AC-11 R2 (call binder + write adjudications into verdict)
- **Change**: Both regular and deferred verdict-construction paths now
  `from adjudication_binding import bind_adjudications`, call the binder, and write
  matched entries into `doc["meta_review"]["adjudications"]` BEFORE
  `redact_forbidden.py` runs.

### 5. `figures/Section1/generate_figures.R`
- **AC ref**: AC-12 R2 (skip cleanup)
- **Change**: New `skip_fig(fig_id, artifact, basename)` helper that `unlink()`s
  `<basename>.png` and `<basename>.pdf` before emitting the warning. All 7 skip
  branches (Fig 2 through Fig 7) migrated to use it. (Fig 1 has no artifact dep.)
- **Verified**: stash `_validation_summary.json` → `Fig5_anti_bias_gauntlet.{png,pdf}`
  deleted with explicit "removed stale: ..." stderr message; restore + rerun →
  Fig 5 regenerates.

## New artifacts (added to LOCKED_ARTIFACTS.json)

- `pipeline/reviewers/adjudication_binding.py` (mutability=forbidden): run-local
  adjudication binder. Loads `pipeline/audits/reviewer_blocker_adjudications.json`,
  validates each entry (required fields + disposition enum), returns matched
  adjudications for a given verdict's propagated blockers by (persona, summary_hash)
  primary match with (persona, round) fallback for explicitly-hashless entries.
  Used by `run_ensemble.sh` (both modes) and by `validate_ensemble_output.py`.

- `pipeline/audits/reviewer_blocker_adjudications.json` (mutability=audit_required):
  canonical machine-readable source for reviewer-blocker adjudications. Codex R1
  flagged this as evidence-controlling input that was NOT in LOCKED. Now locked
  with audit_required policy (it grows append-only as new rounds add adjudications;
  every change requires an engineering audit note like this one).

## Updated artifacts (not locked, just refreshed in this round)

- `FINAL_RESULT.md`: rewritten from current artifacts. Tag SHA, reviewer status,
  adjudication counts read verbatim. AC-1/AC-2/AC-5/AC-7/AC-8/AC-9/AC-10/AC-11/AC-12
  all PARTIAL with concrete reasons. AC-3/AC-4/AC-6 PASS.
- `pipeline/audits/reviewer_blocker_adjudications.md`: added ADJ-003 (R1 new-text),
  ADJ-004 (R2 new-text), ADJ-005 (R4 new-text) corresponding to the three propagated
  blockers in this round's fresh-live verdict. Same conceptual rebuttals as ADJ-001
  (R2 SoC-positioning out-of-scope) and ADJ-002 (R4 D8 by-design).

## Re-lock action
- `pipeline/LOCKED_ARTIFACTS.json`: +2 new entries
  (`adjudication_binding.py` forbidden, `reviewer_blocker_adjudications.json` audit_required);
  refresh hashes for all R2-changed artifacts. Total: ~56.
- `v1.0-methodology-locked` tag: force-move to this R2 close-out commit.
- `runs/round_8/output.json` re-assembled AFTER tag move so `pre_registration_hash`
  equals the new tag SHA.

## Promotion of carry-over AC-5/AC-7/AC-8/AC-9 from Queued to Active

Codex R1 explicitly rejected treating these as queued side issues. The goal tracker
(`.humanize/rlcr/2026-05-27_19-19-06/goal-tracker.md`) now lists them as Active
Tasks, each scheduled for its own dedicated future round. Each is comparable in
scope to R0+R1 combined; bundling more than one per round would risk landing
none well.

## Verification
- `python3 pipeline/reviewers/adjudication_binding.py runs/round_8/reviewer_ensemble_verdict.json`:
  returns matched adjudications.
- `python3 pipeline/reviewers/validate_ensemble_output.py runs/round_8/reviewer_ensemble_verdict.json`:
  PASS (4 adjudications matched, 1 R3 unbound entry recorded honestly).
- Skip-cleanup test (described above): PASS.
- AC-11 walkthrough Step 6 reports `recorded adjudications (verdict=4, ...)`, not
  `verdict=0`. R4 blocker shows `(REBUTTED, ADJ-005 → ...)`.
- `bash scripts/scan_target_leakage.sh pipeline`: PASS.
- `bash scripts/verify_methodology_lock.sh`: PASS post-relock.
- `git rev-parse HEAD == refs/tags/v1.0-methodology-locked^{}` at close-out.
- `runs/round_8/output.json.pre_registration_hash` equals the R2 close-out commit SHA
  (after final re-assembly step).
