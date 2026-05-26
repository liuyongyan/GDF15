# Pre-Registration Manifest — Methodology Lock v1.0

**Lock tag:** `v1.0-methodology-locked`
**Lock date:** 2026-05-27
**Lock authority:** Cheng Lab, Columbia University
**Lock manifest:** [`pipeline/LOCKED_ARTIFACTS.json`](LOCKED_ARTIFACTS.json) (SHA256 per artifact)
**Project goal:** Cell-grade AI discovery pipeline (see `draft.md`)

## Pre-Registration Commitments (carried from draft.md §5.1)

1. **Pre-lock methodology transparency.** Methodology, data sources, scoring formulas, and dimension weights are version-controlled and pinned via the lock tag `v1.0-methodology-locked`. All artifacts listed in `LOCKED_ARTIFACTS.json` are SHA256-pinned at lock time. Iterations before the lock are documented in `git log` and in the per-round summaries under `.humanize/rlcr/.../round-N-summary.md`.

2. **Uniform application of changes.** Any change to a `forbidden`-mutability artifact after the lock is rejected by `scripts/verify_methodology_lock.sh`. Changes to `audit_required`-mutability artifacts are permitted only in Phase β with an `engineering_audit_note.md` endorsed by the Codex review of that round (per AC-1.2).

3. **Honest reporting.** Final scoring results in `FINAL_RESULT.md` are reported as produced by the locked pipeline. No post-lock retuning to elevate any specific target is performed.

## Locked Scoring Methodology

- **Candidate universe**: assembled by `pipeline/universe/build_universe.py` via union over four target-agnostic inclusion rules (Open Targets association ≥ 0.50 for {obesity, T2D, NAFLD, MASH}; GWAS Catalog GW-significant for relevant traits; ChEMBL `max_phase` ≥ 2 in relevant indications; literature `pubmed_count_metabolic` ≥ 50). Universe size at lock: 696 protein-coding gene entries.
- **Scoring dimensions**: 8 dimensions defined in `pipeline/scoring/dimensions.json`. 7 contribute to the composite ranking; `D8_platform_deliverability` is `excluded_from_composite: true` and consumed only by the post-hoc platform-compatibility check.
- **Composite weights**: equal weights of 1/7 across {D1, D2, D3, D4, D5, D6, D7} (precise values in `pipeline/scoring/weights.json`). Sum = 1.0; max single weight = 0.143.

## Locked Anti-Bias Suite

Five mechanisms defined in `pipeline/anti_bias/`:

1. **LOO ablation** — re-rank with each dimension removed; aggregate mean rank change in top-5 must satisfy `max_avg_rank_change_in_top5 = 2.0` (soft).
2. **Negative controls** — known-failed metabolic targets (CB1R/CNR1, CETP, 5-HT2C/HTR2C, DGAT1) must rank below median percentile (≥ 50) on average (soft).
3. **Literature-blinded re-rank** — top-5 overlap with full ranking ≥ 3 of 5 (soft).
4. **Cross-biobank MR** — `OPTIONAL_SKIPPED` allowed with documented reason (multi-biobank harmonization deferred to Phase β if cached summary statistics become available).
5. **Permutation test** — empirical p-value of top-ranked candidate < 0.001 (soft for current bootstrap subset; will tighten with full snapshot in Phase β).

Thresholds in `pipeline/anti_bias/thresholds.json` are target-agnostic; target-specific verifications live in `evaluator/expected_thresholds.json` (read only by the External Evaluator after lock).

## Locked Reviewer Ensemble

Six Cell-reviewer personas defined as prompt files in `pipeline/reviewers/R{1..6}_*.md` + `meta_review.md`. Randomized backbone assignment per round (Codex vs Gemini) deterministic by round number. `FORBIDDEN_TARGET_NAMES.txt` enforces that reviewer outputs do not reference specific target identifiers in prose.

Round 0 used a `MOCK_STUB` ensemble for end-to-end plumbing verification. The validator now rejects `MOCK_STUB` post-lock, so subsequent rounds must invoke real Codex/Gemini calls or use `REVIEWER_DEFERRED` with `RATE_LIMITED.md`.

## Locked External Evaluator

- `evaluator/evaluator.py` is mode-gated: `--mode verbose` requires the lock tag (`v1.0-methodology-locked`) to exist; otherwise rejects with non-zero exit.
- `--mode blind` returns the AC-1.1 categorical JSON contract (no target identifiers, no rank/score gradients).
- `evaluator/expected_answer.json` and `evaluator/expected_thresholds.json` are gitignored (per DEC-1: not disclosed in manuscript; sensitive).

## Pre-Registration Hash Reference

The post-lock Pipeline output's `pre_registration_hash` field is set to the git SHA of the commit bearing the `v1.0-methodology-locked` tag. Any output produced before the lock has `pre_registration_hash` ending with `_pre_lock` and is not AC-2-compliant.

## Reproducibility

A single command from a clean clone reproduces the locked Pipeline output:

```bash
git clone <repo> && cd GDF15
git checkout v1.0-methodology-locked
bash scripts/preflight.sh                # PASS required
bash pipeline/run_pipeline.sh sample_input.json output.json 0
python3 scripts/canonicalize_output.py output.json
diff output.canonical.json <reference_canonical_output>
```

## Disclosure Decision (DEC-1)

Per the user's resolved DEC-1 decision (recorded in `plan.md` §Pending User Decisions), the existence of `evaluator/expected_answer.json` and the Loop's use of this file for calibration is NOT disclosed in the Cell manuscript. `METHODOLOGY_TRANSPARENCY.md` (to be produced at loop end) is an internal-only audit artifact and is not surfaced to readers.

## Future Phase β Allowed Operations

After this lock, the Loop may iterate on `audit_required` artifacts only with the following constraints:

- Each change requires `runs/round_N/engineering_audit_note.md` describing the bug, the fix, and why it does not alter the ranking semantically.
- `scripts/verify_methodology_lock.sh` must pass after every change.
- Phase β may not modify any `forbidden`-mutability artifact under any circumstance.
- Phase β may invoke `evaluator/evaluator.py --mode verbose` to obtain target-aware diagnostics for engineering debugging only.
