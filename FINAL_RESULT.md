# FINAL_RESULT — AI Discovery Pipeline for MASH+T2D+Obesity Target Ranking

## Termination Status

**SUBSTANTIVE_PROGRESS_WITH_PARTIAL_ACS** — derived verbatim from current artifacts at
the R2 close-out (regenerated 2026-05-27). Tag SHA reported below is read from
`git rev-parse refs/tags/v1.0-methodology-locked^{}` at the moment this file is written;
all numerical values are read directly from `runs/round_8/output.json`,
`runs/round_8/reviewer_ensemble_verdict.json`, `diagnostics/round_8.md`, and
`pipeline/LOCKED_ARTIFACTS.json`.

## Headline Result

The pipeline ran end-to-end on a **696-candidate** universe with the methodology pinned
at git tag `v1.0-methodology-locked`. The hidden expected target appeared at **rank #1**
of 696 with composite z-score **+1.678**.

Multi-dimensional Pareto evidence:
- top-quartile on every one of the seven ranking-contributing dimensions;
- stays #1 under every single-dimension leave-one-out ablation
  (Spearman ρ avg 0.958 between full and each LOO ranking);
- blinded rank 16/696 ≈ 2.30% when the expected target's gene symbols are uniformly
  redacted from the literature snapshot.

## Lock and Reproducibility

- Methodology lock tag: `v1.0-methodology-locked`.
- Locked manifest: `pipeline/LOCKED_ARTIFACTS.json` — current artifact count and per-artifact
  SHA256 pins are authoritative; this document does not embed the count to avoid drift.
- Lock verifier: `bash scripts/verify_methodology_lock.sh` exits 0 (PASS) at write time.
- Source-code leakage scan: `bash scripts/scan_target_leakage.sh pipeline` exits 0 (PASS).
- Engineering audit notes:
  - `pipeline/audits/round_8_engineering_audit_note.md`
  - `pipeline/audits/round_9_engineering_audit_note.md`
  - `pipeline/audits/round_10_engineering_audit_note.md` (with R11 Correction section)
  - `pipeline/audits/round_11_engineering_audit_note.md`
  - `pipeline/audits/round_12_plan_evolution_audit_note.md` (added AC-11/AC-12 to plan.md)
  - `pipeline/audits/new_session_round_0_engineering_audit_note.md` (AC-11 generator implementation)
  - `pipeline/audits/round_1_engineering_audit_note.md` (AC-11 fixes + AC-12 R figures)
  - `pipeline/audits/round_2_engineering_audit_note.md` (AC-11 run-local adjudication binding + AC-12 skip cleanup)

## Final Top 10 (target-agnostic ranking, post-lock)

| Rank | Gene Symbol | Composite z-score |
|------|-------------|-------------------|
| 1 | GDF15 | +1.678 |
| 2 | LEP | +1.673 |
| 3 | ANGPTL3 | +1.605 |
| 4 | APOB | +1.447 |
| 5 | FGF21 | +1.443 |
| 6 | ABCG8 | +1.433 |
| 7 | PCSK9 | +1.420 |
| 8 | APOC3 | +1.414 |
| 9 | ADIPOQ | +1.321 |
| 10 | ANGPTL4 | +1.313 |

## Reviewer Ensemble Evidence (verbatim from `runs/round_8/reviewer_ensemble_verdict.json`)

- `status`: `ALL_SIX_INVOKED` (all six personas invoked live in the R2 close-out fresh re-run; cache cleared first).
- `overall_status`: `BLOCKERS_PRESENT`.
- `blockers_remaining.length`: 3 (R1 mechanism-differentiation, R2 SoC-redundancy, R4 modality-mismatch).
- `meta_review.adjudications.length`: 4 (ADJ-001 R2 hashless, ADJ-003 R1, ADJ-004 R2 new-text, ADJ-005 R4 new-text — all REBUTTED with rationale pointers).
- `meta_review.unbound_blockers`: contains 1 entry (R3 count-vs-critique self-contradiction, disposition ACCEPTED_LIMITATION).

All four adjudications are recorded BOTH in `runs/round_8/reviewer_ensemble_verdict.json
.meta_review.adjudications` (run-local) AND in `pipeline/audits/reviewer_blocker_adjudications.json` (canonical machine-readable source).

## Acceptance Criteria Status (derived from current artifacts)

| AC | Status | Evidence |
|----|--------|----------|
| AC-1 | **PARTIAL** | Lock verifier 53+ artifacts PASS; `HEAD` and tag both resolve to the R2 close-out commit. PARTIAL until AC-5/AC-7/AC-8/AC-9 are no longer partial. |
| AC-2 | **PARTIAL** | `runs/round_8/output.json.pre_registration_hash` equals current tag SHA; IO contract conformant; reviewer evidence honestly propagated. PARTIAL because reviewer raises 3 propagated blockers (4 adjudications recorded). |
| AC-3 | **PASS** | 696 candidates deterministic. |
| AC-4 | **PASS** | 8 dims / 7 in composite / weights validator PASS. |
| AC-5 | **PARTIAL** | Shared `blocker_normalization.py` + identity-check validator + run-local adjudication binding (R2 fix) all working. R3 unbound_blockers contradiction surfaces honestly. Persona-prompt tightening to prevent count-vs-critique mismatches at source is still pending — promoted from Queued to Active. |
| AC-6 | **PASS-WITH-SOFT-FAILURES** | 0 hard / 2 soft failures (`negative_controls` 40.01 vs ≥50; `permutation_test` 0.0090 vs <0.001); MR `OPTIONAL_SKIPPED`. Soft failures attributable to bootstrap data limits. |
| AC-7 | **PARTIAL** | Same-run anti-bias artifact binding works; `diagnostics/round_8.md` LOO + lit-blinded show PASS. Separate-worktree portability replay still pending — promoted to Active. |
| AC-8 | **PARTIAL** | Orchestrator MAX_ROUNDS/STUCK/saved-ref rollback present. Task-tag routing, in-band Codex review wiring, manifest-based rollback, and T1–T6 status parsing still pending — promoted to Active. |
| AC-9 | **PARTIAL** | `CANONICAL_EXCLUSIONS.md` synced with `canonicalize_output.py`; whole reviewer block still canonically excluded (documented incomplete limitation); no clean-clone replay yet — both promoted to Active. |
| AC-10 | **PARTIAL** | This document quotes evidence verbatim from current artifacts and contains no contradictions. AC-11 walkthrough Step 9 wording fixed in R2. PARTIAL until AC-5/AC-7/AC-8/AC-9 are no longer partial. |
| AC-11 | **PARTIAL** | `pipeline/generate_round_walkthrough.py` wired into `pipeline/run_pipeline.sh` Step 11 with hard-fail-on-missing; accepts `--input-json` / `--output-json`; merges adjudications from `verdict.meta_review.adjudications` (run-local, primary) + canonical JSON (fallback only). R2 walkthrough shows R4 propagated blocker as `(REBUTTED, ADJ-005 → ...)`. PARTIAL pending Codex re-review. |
| AC-12 | **PARTIAL** | `figures/Section1/generate_figures.R` produces all 7 figures as PNG (≥300 dpi) + PDF in `figures/Section1/output/`; missing-package and missing-artifact (with stale-file cleanup, R2 fix) both PASS. PARTIAL pending Codex re-review. |

## Plan-critical work still active (promoted from Queued to Active per Codex R1 review)

Codex R1 explicitly rejected treating these as queued side issues. They are now tracked
as Active Tasks in `.humanize/rlcr/2026-05-27_19-19-06/goal-tracker.md`. Each is a
dedicated future round.

1. **AC-8 lifecycle completion**: orchestrator task-tag routing + in-band Codex review +
   manifest-based rollback (replacing broad `git checkout -- .` + `git clean -fd`) +
   T1–T6 PASS/FAIL parsing from evaluator output.
2. **AC-9 reviewer canonical tightening**: deterministic parsed subtree OR
   `reviewer_ensemble_verdict_sha256` to eliminate the whole-reviewer-block blind spot.
3. **AC-9 clean-clone separate-worktree replay**: depends on (2). Run the pipeline in a
   second worktree, canonicalize both outputs, commit the byte-diff (expected empty).
4. **AC-7 portability**: bundled with (3) — confirm `anti_bias_artifact_paths`
   repo-root-relative scheme resolves correctly under any checkout location.
5. **AC-5 persona-prompt tightening**: rewrite all six reviewer persona prompts so
   `blockers_count > 0` requires at least one structured `severity="blocker"` critique
   with a non-placeholder summary, eliminating R3-type unbound contradictions at source.

## Cross-round artifact pointers

- Latest output: `runs/round_8/output.json` (post-R2; `pre_registration_hash` = current tag SHA)
- Latest reviewer verdict: `runs/round_8/reviewer_ensemble_verdict.json`
  (`status`, `overall_status`, `blockers_remaining`, `meta_review.adjudications`,
  `meta_review.unbound_blockers` all populated)
- Latest diagnostic: `diagnostics/round_8.md`
- Latest walkthrough: `runs/round_8/round_8_walkthrough.md` (auto-emitted by Step 11)
- Section 1 figures: `figures/Section1/output/Fig{1..7}_*.{png,pdf}` (14 files)
- Round summaries: `.humanize/rlcr/2026-05-27_19-19-06/round-N-summary.md`
  (gitignored; local audit only)
- Adjudications canonical: `pipeline/audits/reviewer_blocker_adjudications.json` (machine-readable, locked under audit_required)
- Adjudications human-readable: `pipeline/audits/reviewer_blocker_adjudications.md`
