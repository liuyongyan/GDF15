# Engineering Audit Note — Round 1 (new RLCR session) — 2026-05-27

## Purpose
Round 1 closes out task29 (AC-11 fixes per Codex R0 review) AND task30 (AC-12 R figures)
AND task31 (final re-lock + tag move + regen) in one bundle, per Codex R0's required-
implementation plan. Codex rejected R0's attempt to defer task30 to a later round.

Three Codex R0 findings addressed:
1. AC-11 walkthrough lacked adjudication propagation for R4 blocker (showed `UNADJUDICATED`).
2. AC-11 walkthrough hard-coded `sample_input.json` and `runs/round_N/output.json` paths.
3. AC-12 (task30) was completely unimplemented.

## Forbidden-mutability artifacts changed (1)

### 1. `pipeline/generate_round_walkthrough.py`
- **AC ref**: AC-11
- **Change**:
  - Added `--input-json` and `--output-json` CLI options; falls back to defaults only when omitted.
  - Step 1 prose + results reports `args.input_json` (or the relative-to-repo display path).
  - Step 7 prose + results reports `args.output_json`; reads the output JSON from the supplied path.
  - Adjudications now merged from BOTH `verdict.meta_review.adjudications` AND
    `pipeline/audits/reviewer_blocker_adjudications.json` (canonical JSON wins on hash conflict).
  - Hashless adjudications (e.g., ADJ-001 with `blocker_summary_hash=null`) indexed by
    (persona, round) for fallback matching.
  - Walkthrough Step 6 results section reports both verdict and canonical-JSON counts,
    plus the merged unique-by-hash count, plus disposition with adjudication-id and
    rationale-pointer for each propagated blocker.
- **Why**: Codex R0 Findings 1 + 2. Adjudication propagation must survive verdict
  regeneration; walkthrough must reflect actual pipeline invocation paths.
- **Verification**:
  - Direct test: `python3 pipeline/generate_round_walkthrough.py --round 8
    --input-json /custom/path/my-input.json --output-json /tmp/ac11-custom-output.json
    --out /tmp/test.md` → Step 1 shows `/custom/path/my-input.json`, Step 7 shows
    `/tmp/ac11-custom-output.json`.
  - Run on `runs/round_8`: Step 6 shows "Propagated blockers: 1; recorded
    adjudications (verdict=0, canonical JSON=2, merged unique by hash=1)" and the R4
    blocker shows "(REBUTTED, ADJ-002 → pipeline/audits/reviewer_blocker_adjudications.md#ADJ-002)".
- **Target-blind**: yes.

## Audit_required artifacts changed (1)

### 2. `pipeline/run_pipeline.sh`
- **AC ref**: AC-11
- **Change**: Step 11 invocation extended with `--input-json "$INPUT_JSON" --output-json "$OUTPUT_JSON"`.
- **Why**: Codex R0 Finding 2 — Step 11 must pass the actual pipeline invocation paths.

## New artifacts (none added to LOCKED_ARTIFACTS)

- `pipeline/audits/reviewer_blocker_adjudications.json`: canonical machine-readable
  source for reviewer-blocker adjudications. Companion to the existing `.md` file.
  Consumed by `generate_round_walkthrough.py`. Contains ADJ-001 (R2, hashless,
  matched by persona+round) and ADJ-002 (R4, matched by hash `1e70f8466ac4753e`).
  Not added to LOCKED_ARTIFACTS because it grows with each adjudicated round
  (append-only audit artifact, like the `.md` companion). The walkthrough generator
  cross-references it.

- `figures/Section1/generate_figures.R` (AC-12 task30): R script producing the seven
  Section 1 figures as PNG (≥300 dpi) + PDF in `figures/Section1/output/`. Reads from
  `runs/round_N/output.json`, `reviewer_ensemble_verdict.json`,
  `anti_bias/_results_*.json`, `_validation_summary.json`,
  `platform_compatibility_top25.tsv`, and `pipeline/audits/reviewer_blocker_adjudications.json`.
  Missing-package detection at startup. Missing-artifact skip-with-warning behavior.
  CLI `--round N` (default: latest numeric `runs/round_N`).
  Verified: ggplot2 4.5.2, scales 1.3.0, cowplot 1.1.3, jsonlite, dplyr, tidyr present.
  Output directory created with all 14 files (7 PNG + 7 PDF). Sample Fig 3 (per-dim
  heatmap, 25 candidates × 8 dims) is publication-quality.
  Not added to LOCKED_ARTIFACTS because figures/ is presentation-layer (not part of
  the ranking pipeline). The R script's behavior is governed by AC-12 acceptance
  tests, not SHA pinning.

- `figures/Section1/README.md`: lists R-package dependencies (ggplot2, scales, cowplot,
  jsonlite, dplyr, tidyr), per-figure data sources, regeneration command, and the
  target-blind constraint.

- `figures/Section1/output/Fig{1..7}_*.{png,pdf}`: 14 generated figures (committed to git per AC-12).

## Files updated

- `FINAL_RESULT.md`: AC-10 evidence updated to reference `Fig{1..7}_*.png` / `.pdf`
  instead of legacy `.md` sketches. AC-11 and AC-12 rows added with PARTIAL status
  and current artifact evidence.

## Re-lock action
- `pipeline/LOCKED_ARTIFACTS.json`: refresh hashes for the two changed locked artifacts
  (`pipeline/generate_round_walkthrough.py` forbidden, `pipeline/run_pipeline.sh`
  audit_required). No new entries; total remains 54.
- `v1.0-methodology-locked` tag: force-move to this R1 close-out commit.
- `runs/round_8/output.json` regenerated AFTER the tag move so `pre_registration_hash`
  equals the new tag SHA (assemble_output only, not the full pipeline, to preserve the
  R1 live-rerun reviewer verdict).

## Out of scope (still Queued)
Carry-overs from prior session, deliberately not addressed this round to keep the
AC-11/AC-12 bundle tight: AC-8 lifecycle full completion, AC-9 clean-clone replay,
AC-9 reviewer canonical tightening, AC-5 persona-prompt tightening,
`scripts/scan_api_calls.sh` zero-on-detect.
