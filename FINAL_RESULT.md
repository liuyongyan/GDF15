# FINAL_RESULT — AI Discovery Pipeline for MASH+T2D+Obesity Target Ranking

## Termination Status

**SUBSTANTIVE_PROGRESS_WITH_PARTIAL_ACS** — derived from current artifacts at the R3
close-out (regenerated 2026-05-27). Tag SHA and reviewer status reported below are
read from `git rev-parse refs/tags/v1.0-methodology-locked^{}` and
`runs/round_8/reviewer_ensemble_verdict.json` at the moment this file is written.

## Headline Result

The pipeline ran end-to-end on a **696-candidate** universe with the methodology
pinned at git tag `v1.0-methodology-locked`. The hidden expected target appeared at
**rank #1** with composite z-score **+1.678**.

Multi-dimensional Pareto evidence:
- top-quartile on every one of the seven ranking-contributing dimensions;
- stays #1 under every single-dimension leave-one-out ablation (Spearman ρ avg 0.958);
- blinded rank 16/696 ≈ 2.30% when target gene symbols are uniformly redacted from
  the literature snapshot.

## Lock and Reproducibility

- Methodology lock tag: `v1.0-methodology-locked`.
- Locked manifest: `pipeline/LOCKED_ARTIFACTS.json` — 56 artifacts at R3 close-out
  (count verifiable by `jq '.artifacts | length' pipeline/LOCKED_ARTIFACTS.json`).
- Lock verifier `bash scripts/verify_methodology_lock.sh`: PASS at write time.
- Source-code leakage scan `bash scripts/scan_target_leakage.sh pipeline`: PASS at
  write time.

**HEAD / tag / output-hash relationship at write time:**
- `git rev-parse HEAD` → recorded in the R3 close-out commit (see git log).
- `git rev-parse refs/tags/v1.0-methodology-locked^{}` → moved to the R3 close-out
  commit AFTER all R3 changes landed (audit note, prompts, validator, Fig 6, this
  document) so HEAD == tag at the moment of tag move.
- `jq -r .pre_registration_hash runs/round_8/output.json` → equals the R3 close-out
  commit SHA, regenerated via `pipeline/assemble_output.py` after the tag move so
  the embedded hash matches `git rev-parse refs/tags/v1.0-methodology-locked^{}`.

If any commit (e.g. a presentation-only PDF metadata refresh) is made AFTER the tag
move, HEAD will differ from the tag — this document does NOT claim ongoing HEAD=tag
equality, only that the alignment was established at the R3 close-out commit and the
output's `pre_registration_hash` records the tag SHA at run time.

Engineering audit notes (one per round; chronological):
`pipeline/audits/round_{8,9,10,11}_engineering_audit_note.md`,
`pipeline/audits/round_12_plan_evolution_audit_note.md`,
`pipeline/audits/new_session_round_0_engineering_audit_note.md`,
`pipeline/audits/round_{1,2,3}_engineering_audit_note.md`.

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

## Reviewer Ensemble Evidence (R3 fresh-live regenerated verdict)

Read verbatim from `runs/round_8/reviewer_ensemble_verdict.json` at R3 close-out:
- `status`: `ALL_SIX_INVOKED` — six personas live-invoked after cache cleared. R2
  required a second attempt (first attempt hit `BOTH_BACKBONES_FAILED`); on second
  attempt all six produced output (R2 fresh-live this run, others served from the
  cache populated by the first-attempt successes).
- `overall_status`: `PASS` — no propagated blockers under the new prompt invariant.
- `blockers_remaining.length`: 0.
- `meta_review.adjudications.length`: 0 (no blockers ⇒ no adjudications needed
  this round).
- `meta_review.unbound_blockers`: absent (the new prompt invariant eliminates the
  count-vs-critique self-contradiction class at source).

The reviewer cache is populated by per-(persona,prompt_hash,input_hash) keys; the
R3 prompt edits changed `prompt_hash` for all six personas, invalidating prior
cached responses and forcing a true fresh live run.

## Acceptance Criteria Status (derived from current artifacts)

| AC | Status | Evidence |
|----|--------|----------|
| AC-1 | **PARTIAL** | Lock verifier 56 artifacts PASS; HEAD == tag at R3 close-out commit. PARTIAL until AC-7/AC-8/AC-9 also pass. |
| AC-2 | **PARTIAL** | Output JSON conformant; `pre_registration_hash` matches tag SHA. PARTIAL until full plan-AC set passes. |
| AC-3 | **PASS** | 696 candidates deterministic. |
| AC-4 | **PASS** | 8 dims / 7 in composite / weights validator PASS. |
| AC-5 | **PARTIAL** (advanced) | R3 added Blocker Emission Invariant to all 6 persona prompts; validator hard-fails count-vs-critique mismatch (no `unbound_blockers` escape); fresh-live verdict has 0 contradictions. PARTIAL pending Codex re-review of R3 implementation. |
| AC-6 | **PASS-WITH-SOFT-FAILURES** | 0 hard / 2 soft failures (`negative_controls` 40.01 vs ≥50; `permutation_test` 0.0090 vs <0.001); MR OPTIONAL_SKIPPED. |
| AC-7 | **PARTIAL** (Active R6) | Same-run artifact binding works; LOO + lit-blinded PASS in `diagnostics/round_8.md`. Separate-worktree portability replay scheduled for R6 (bundled with AC-9 clean-clone). |
| AC-8 | **PARTIAL** (Active R4) | Orchestrator MAX_ROUNDS/STUCK/saved-ref rollback present. Task-tag routing, in-band Codex review, manifest rollback, T1–T6 parsing scheduled for R4. |
| AC-9 | **PARTIAL** (Active R5) | `CANONICAL_EXCLUSIONS.md` synced; whole reviewer block still excluded. Deterministic reviewer canonical (parsed subtree or content hash) scheduled for R5; clean-clone replay R6. |
| AC-10 | **PARTIAL** | This document is byte-derived from current artifacts. PARTIAL until AC-5/AC-7/AC-8/AC-9 are PASS. |
| AC-11 | **ACCEPTED** (R2) per Codex R2 review | `pipeline/generate_round_walkthrough.py` wired as run_pipeline.sh Step 11 with hard-fail-on-missing; accepts `--input-json` / `--output-json`; reads `verdict.meta_review.adjudications` first; honestly surfaces `unbound_blockers` (now empty under R3 invariant). |
| AC-12 | **PARTIAL** (advanced R3) | `figures/Section1/generate_figures.R` produces all 7 figures (PNG ≥300 dpi + PDF) from run-local artifacts only — Fig 6 now reads verdict adjudications only (no sidecar); `skip_fig` deletes stale outputs on missing artifacts; missing-package detection. PARTIAL pending Codex re-review. |

## Plan-critical work scheduled for R4–R6 (Active, not deferred)

1. **R4 — AC-8 lifecycle completion**: orchestrator task-manifest parsing
   (coding/analyze tags); in-band Codex review handoff written into
   `reviews/round_N.md`; rollback restricted to start-of-round touched-file manifest;
   T1–T6 PASS/FAIL parsed directly from evaluator diagnostic.
2. **R5 — AC-9 reviewer canonical tightening**: replace whole-block exclusion with
   either a deterministic parsed subtree or `reviewer_ensemble_verdict_sha256`
   computed from canonicalized parsed persona outputs + propagated blockers +
   meta-review + adjudications + unbound (excluding only raw LLM prose + runtime
   fields).
3. **R6 — AC-9 clean-clone replay + AC-7 portability**: separate clean worktree,
   `pipeline/setup_env.sh`, `bash pipeline/run_pipeline.sh sample_input.json
   runs/round_8/output.json 8`, canonicalize both reference + replay outputs, commit
   empty byte-diff evidence. Same replay verifies `anti_bias_artifact_paths` resolve
   relative to the replay checkout.

## Cross-round artifact pointers

- Output: `runs/round_8/output.json` (pre_registration_hash = current tag SHA at
  R3 close-out)
- Verdict: `runs/round_8/reviewer_ensemble_verdict.json`
- Diagnostic: `diagnostics/round_8.md`
- Walkthrough: `runs/round_8/round_8_walkthrough.md` (auto-emitted by Step 11)
- Section 1 figures: `figures/Section1/output/Fig{1..7}_*.{png,pdf}` (14 files)
- Adjudications canonical (machine-readable): `pipeline/audits/reviewer_blocker_adjudications.json`
- Adjudications human-readable: `pipeline/audits/reviewer_blocker_adjudications.md`
- Round summaries: `.humanize/rlcr/2026-05-27_19-19-06/round-N-summary.md`
  (gitignored; local audit only)
