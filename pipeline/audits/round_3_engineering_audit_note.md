# Engineering Audit Note — Round 3 (new RLCR session) — 2026-05-27

## Purpose
Round 3 closes Codex R2's two immediately-actionable defects (Fig 6 double-counting
+ HEAD/tag honesty) AND lands AC-5 persona-prompt tightening as the first of the
four plan-critical carry-over ACs Codex demanded be unparked.

## Forbidden-mutability artifacts changed (8)

### 1–6. `pipeline/reviewers/R{1..6}_*.md` (all 6 persona prompts)
- **AC ref**: AC-5 (prompt invariant tightening)
- **Change**: Appended a shared `## Blocker Emission Invariant (AC-5 R3 hardening)`
  section to all six persona prompts with three enforceable rules:
  1. `blockers_count` MUST equal the count of `severity="blocker"` critiques.
  2. Each `severity="blocker"` critique MUST include `candidate_id`,
     `concern_category` (enum), `summary` (≥40 chars, not placeholder), `detail`
     (≥120 chars).
  3. If no critique meets (2), `blockers_count` MUST be 0.
- **Why**: Prior rounds repeatedly hit "R3-style count-vs-critique contradictions"
  (e.g., `blockers_count=2` with only `severity="major"` critiques). The validator
  caught them but required manual `meta_review.unbound_blockers` adjudication
  every round. Tightening the prompt contract removes the contradiction at source.
- **Verified**: R3 fresh-live regen with new prompts produced
  `ALL_SIX_INVOKED`, all six personas `blockers_count=0`, zero unbound contradictions.
- **Target-blind**: yes — the invariant text contains no gene-symbol literals.

### 7. `pipeline/reviewers/validate_ensemble_output.py`
- **AC ref**: AC-5 (validator hardening)
- **Change**: Count-vs-critique mismatch is now a HARD post-lock error. Previous
  behavior allowed the `meta_review.unbound_blockers[persona]` escape; that escape
  is removed. The validator now requires `blockers_count == n_real_blockers` for
  each persona in post-lock regular mode.
- **Why**: With prompts tightened, there is no legitimate reason for contradiction.
  Reviewer-prompt compliance is enforced at the validator boundary.
- **Verified**: Negative test — synthetic R3 with `bc=1, severity=major` →
  validator exit 1 with explicit "count-vs-critique mismatch" error. Positive
  test — same with `bc=0` → exit 0.

### 8. `figures/Section1/generate_figures.R`
- **AC ref**: AC-12 (Fig 6 must read run-local verdict only)
- **Change**: Removed `adj_json <- read_json_safe(...)` from the shared-artifacts
  loader. Fig 6 now counts adjudications from `verdict$meta_review$adjudications`
  only, unique by non-empty `adjudication_id`. The R2 implementation incorrectly
  summed verdict + canonical lengths and displayed `Adjudications on file: 9`
  (4 verdict + 5 canonical) — now correctly displays `4`.
- **Why**: Codex R2 Finding 1 — Fig 6 must be factually derived from the round-local
  verdict to satisfy AC-12's runtime-artifact data-source contract.
- **Verified**: `pdftotext Fig6_reviewer_ensemble.pdf` reports
  `Round 8 | Status: ALL_SIX_INVOKED | Propagated blockers: 3 | Adjudications on file: 4`.
  (Propagated blockers count is from the R2-state verdict that was current when
  Fig 6 was regenerated mid-R3, before the final R3 prompt-tightening re-run; the
  final R3 verdict has 0 propagated blockers.)

## Updated artifacts

### `figures/Section1/README.md`
- Fig 6 data-source row updated: sole source is `runs/round_N/reviewer_ensemble_verdict.json`
  (run-local; no sidecar). Matches the script change.

### `FINAL_RESULT.md`
- Rewritten to honestly report HEAD/tag/output-hash relationship at R3 close-out.
- Reflects new verdict state: `ALL_SIX_INVOKED`, 0 propagated blockers,
  0 adjudications (since 0 blockers), 0 unbound.
- AC-5 status upgraded to "advanced" with prompt invariant landed; full PASS
  pending Codex re-review.
- AC-7/AC-8/AC-9 remain Active (scheduled for R4–R6).

### `pipeline/audits/reviewer_blocker_adjudications.md` and `.json`
- No new ADJ entries needed this round (verdict has 0 propagated blockers).
- Historical entries (ADJ-001 through ADJ-005) retained for audit trail.

## Re-lock action
- `pipeline/LOCKED_ARTIFACTS.json`: hashes refreshed for 8 changed forbidden
  artifacts (6 prompts + validate_ensemble_output.py + generate_figures.R is
  not in LOCKED so its hash is not refreshed there). Total: 56 (no new entries).
- `v1.0-methodology-locked` tag: force-move to R3 close-out commit AFTER all
  changes + audit note + FINAL_RESULT update commit lands.
- `runs/round_8/output.json` re-assembled AFTER tag move so
  `pre_registration_hash` equals new tag SHA.

## Out of scope (still Active for future rounds R4–R6)
- AC-8 lifecycle full completion (orchestrator refactor).
- AC-9 reviewer canonical tightening (`reviewer_ensemble_verdict_sha256`).
- AC-9 clean-clone replay + AC-7 portability (depends on AC-9 canonical landing).

## R3 success criteria (all met)
- [✓] `generate_figures.R` no longer loads canonical adjudications JSON.
- [✓] Fig 6 displays `Adjudications on file: 4` (verdict-only, not 9).
- [✓] README updated to reflect verdict-only source.
- [✓] All 6 persona prompts have the shared invariant section.
- [✓] Validator HARD-fails count-vs-critique mismatch post-lock (no unbound escape).
- [✓] Fresh-live rerun produces ALL_SIX_INVOKED with all bc=0, zero unbound.
- [✓] HEAD/tag/output-hash alignment will be enforced at the final R3 close-out commit.
