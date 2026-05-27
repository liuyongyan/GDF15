# Plan v1.1: Two-Phase Autonomous Loop for Designing a Cell-Grade AI Discovery Pipeline that Rediscovers GDF15

## Goal Description

Build and execute an autonomous design loop that produces (a) a methodologically pre-registered AI discovery pipeline ranking protein targets for the obesity + type 2 diabetes + metabolic-associated steatohepatitis (MASH) indication, (b) an auditable separation between methodology-design iteration (target-blind) and engineering-iteration after methodology lock (target-aware for debugging only), and (c) a Cell-grade artifact bundle including ranked output, anti-bias gauntlet results, a six-persona simulated peer-review trace, post-hoc platform-compatibility analysis, single-command reproducibility envelope, and a `FINAL_RESULT.md` summarizing whether the expected outcome (GDF15 in the top tier of the ranking with platform compatibility confirmed) was reached.

The loop is intended to run unattended overnight (target wall-clock 6–8 hours). The user reviews the final state in the morning.

The architecture is **two-phase** to address the central methodological risk that an evaluator iterating against a known expected target can become indirect target-rigging:

- **Phase α — Methodology Design (evaluator-free).** The Loop iterates on pipeline methodology (candidate universe rules, scoring dimensions, scoring formulas, anti-bias mechanisms, reviewer-ensemble prompts) WITHOUT ever invoking the External Evaluator. The evaluator is not called even in blind mode. Convergence is judged by: (a) Codex methodological critique declaring no further REQUIRED_CHANGES; (b) the six-persona reviewer ensemble running on a small generic validation sub-universe (e.g., 50 protein targets sampled from the candidate-universe builder, NOT including or referencing GDF15) and producing no blocker-level critiques on the methodology; (c) all schema validators and leakage scanners passing. Phase α terminates when these three signals align. Methodology is then locked via `git tag v1.0-methodology-locked`; SHA256 hashes of every locked artifact are recorded in `pipeline/PRE_REGISTRATION.md` and in `pipeline/LOCKED_ARTIFACTS.json`.
- **Phase β — Engineering Iteration (post-lock).** The Loop runs the locked Pipeline end-to-end on the full candidate universe and invokes the External Evaluator in `--mode verbose`. Iteration is allowed ONLY on engineering concerns: bug fixes, schema compliance, missing-data handling, dependency pins, runtime/performance, and reviewer-prompt typo-level edits. Forbidden-change detection is performed by Codex every round using both (1) diff-pattern checks against locked source patterns and (2) SHA256 comparison of touched files against `LOCKED_ARTIFACTS.json`. Any Phase β change that materially alters the Pipeline's ranking output (even via "missing-data handling") must be accompanied by an engineering-audit note explaining the bug and why the fix is non-substantive; Codex must endorse the note.

## Acceptance Criteria

Following TDD philosophy, each criterion includes positive and negative tests for deterministic verification.

- AC-1: Two-Phase Loop Architecture is implemented with an explicit, irrevocable methodology lock between Phase α and Phase β.
  - Positive Tests (expected to PASS):
    - `pipeline/PRE_REGISTRATION.md` exists, references the `v1.0-methodology-locked` git tag, and contains a manifest of locked artifacts (dimension list, weights, candidate-universe construction script path, anti-bias thresholds, reviewer prompts paths).
    - The Loop log (`LOOP_SUMMARY.md`) shows at least one Phase α round preceding the tag and at least one Phase β round following it.
    - Any attempted post-lock edit to a locked-artifact file is rejected by an automated check (e.g., `scripts/verify_methodology_lock.sh` returns non-zero exit).
  - Negative Tests (expected to FAIL):
    - A test harness that attempts to modify `pipeline/scoring/weights.json` after the lock tag must produce a non-zero exit from `scripts/verify_methodology_lock.sh`.
    - A test harness that tries to advance to Phase β without first creating the lock tag is rejected by the orchestrator.
  - AC-1.1: Phase α uses a Blind Evaluator that returns only categorical pass/fail per criterion, with no target-specific gradient information.
    - Positive: `evaluator/evaluator.py --mode blind` returns a JSON containing only `{T1_pass: bool, T2_pass: bool, T3_pass: bool, T4_pass: bool, T5_pass: bool, T6_pass: bool}` with no target identifiers, no rank deltas, no per-dimension contribution figures.
    - Negative: the blind-mode output must NOT contain strings matching `GDF15`, `GFRAL`, `MIC-1`, `NAG-1`, or any per-dimension numeric contribution to GDF15's rank.
  - AC-1.2: Phase β uses a Verbose Evaluator that may return rich debugging info to assist engineering iteration on the post-lock Pipeline.
    - Positive: `evaluator/evaluator.py --mode verbose` returns the full diagnostic schema including per-dimension contributions and ranking analysis.
    - Negative: Verbose-mode invocations during Phase α (before the lock tag) must be rejected by the orchestrator with a clear error.

- AC-2: Inner AI Discovery Pipeline implements the IO contract specified in the draft §3.1.
  - Positive Tests (expected to PASS):
    - `pipeline/run_pipeline.sh` accepts a path to an input JSON matching the schema in draft §3.1 and writes an output JSON to a path matching draft §3.1's output schema.
    - The output JSON includes at least 25 ranked targets, all anti-bias mechanism fields enumerated in draft §6 (LOO ablation, negative controls, literature-blinded re-rank, cross-biobank replication or its documented OPTIONAL-skip note, permutation test), and the full reviewer-ensemble verdict (six personas plus meta-review).
    - The output JSON contains `pre_registration_hash` matching the current `v1.0-methodology-locked` git SHA.
  - Negative Tests (expected to FAIL):
    - Running the Pipeline against an input JSON missing required fields rejects with a validation error.
    - The Pipeline source tree (excluding `evaluator/`) contains no string match for `GDF15`, `GFRAL`, `MIC-1`, `NAG-1` (case-insensitive). Detected by `scripts/scan_target_leakage.sh`.
    - The Pipeline must not call `evaluator/expected_answer.json` from any code path outside `evaluator/`.
  - AC-2.1: The Pipeline prefers cached public data sources but MAY make live API calls in either Phase α or Phase β (per DEC-3 resolution). Every live call is logged for audit and cached for replay.
    - Positive: Cached snapshots at `pipeline/data_sources/snapshots/` are checked first; cache miss triggers documented live fetch with response written back to cache.
    - Positive: All non-LLM live HTTP calls are recorded in `runs/round_N/api_calls.log` (JSON-lines: timestamp, endpoint, request hash, status code, cached-path).
    - Negative: Pipeline-side code that issues an undocumented network call (no entry in `api_calls.log`) is flagged by `scripts/scan_api_calls.sh` (best-effort static analysis grep for `requests.get`, `urllib`, `httpx`, `curl`, `wget` in Pipeline source).

- AC-3: Candidate Universe is constructed by a deterministic, documented, target-agnostic algorithm before any scoring runs.
  - Positive Tests (expected to PASS):
    - `pipeline/universe/build_universe.py` produces `pipeline/universe/candidate_universe.tsv` with between 500 and 2000 protein-coding genes, sourced via union over Open Targets associations to obesity/T2D/MASH, GWAS Catalog associations for BMI/HbA1c/ALT/liver-fat at genome-wide significance, ChEMBL targets of approved or Phase 2+ metabolic compounds, and curated literature targets (the literature curation is rule-based, e.g., "secreted hormones with PubMed counts > N in MASH/obesity context", NOT a hand-picked list).
    - The universe builder is deterministic: running it twice on the same cached inputs produces identical output (verified by SHA256).
    - The universe contains a broad therapeutic-class distribution: kinases, receptors, secreted ligands, transcription factors, etc. (validated by an automated diversity check requiring at least 3 distinct UniProt-derived class buckets each contributing >5% of the universe).
  - Negative Tests (expected to FAIL):
    - Running the builder against an empty `pipeline/data_sources/` directory must produce an explicit error, not silently return an empty universe.
    - The builder rejects manual additions of any specific gene by symbol; only the documented inclusion rules may select candidates.
    - `scripts/scan_target_leakage.sh` invoked on `pipeline/universe/` must return zero hits for forbidden target names (GDF15, GFRAL, MIC-1, NAG-1).
    - (target-aware verification of GDF15 presence in the universe is performed only by `evaluator/evaluator.py` after the lock, not as a Pipeline-side AC).

- AC-4: Scoring layer defines at least five orthogonal dimensions, each with a deterministic scoring formula, normalization rule, and missingness policy.
  - Positive Tests (expected to PASS):
    - `pipeline/scoring/dimensions.json` enumerates between 5 and 10 dimensions; the file is referenced by `PRE_REGISTRATION.md` and frozen at lock.
    - `pipeline/scoring/weights.json` defines a weight for each ranking-contributing dimension; weights sum to 1.0 (±1e-6); no single weight exceeds 0.40.
    - The platform-deliverability dimension is present, marked `excluded_from_composite: true`, and only consumed by the post-hoc check.
    - Every dimension's score function emits a value in [-3.0, 3.0] (z-score-like) plus a missingness flag.
  - Negative Tests (expected to FAIL):
    - Loading a `weights.json` whose sum deviates from 1.0 by more than 1e-6 is rejected by `pipeline/scoring/validate_weights.py`.
    - Any dimension whose name or formula introduces target-specific logic (matches `GDF15`/`GFRAL`/family-specific receptor checks) is flagged by `scripts/scan_target_leakage.sh`.

- AC-5: Six-Persona Cell Reviewer Ensemble is integrated as an Inner Pipeline component with versioned, randomized-backbone prompts and graceful rate-limit degradation.
  - Positive Tests (expected to PASS):
    - `pipeline/reviewers/` contains six prompt files `R1_molecular_biologist.md` through `R6_editor.md`, each with a documented persona, evaluation rubric, and blocker-definition section. Also `pipeline/reviewers/FORBIDDEN_TARGET_NAMES.txt` lists target identifiers the reviewer must NEVER explicitly mention by name (GDF15, GFRAL, MIC-1, NAG-1); reviewers reference candidates by anonymized ID until the final user-facing report.
    - The ensemble's invocation script `pipeline/reviewers/run_ensemble.sh` performs RANDOMIZED backbone assignment per round: for each round, each of the six personas is randomly assigned to one of {`codex` (gpt-5.5), `gemini` (3.1-pro)} with uniform probability, recorded in `runs/round_N/reviewer_backbone_assignment.json`. A deterministic seed derived from the round number is documented for replay.
    - On rate-limit error from one backbone, the ensemble re-routes the affected persona to the other backbone with a WARNING logged; if BOTH backbones are rate-limited, falls back to (a) cached reviewer outputs keyed by prompt-hash + input-hash if available, then (b) deferred-reviewer mode that flags the round as `REVIEWER_DEFERRED` and writes `RATE_LIMITED.md` with the relevant `*_API_KEY` env var instructions.
    - The output JSON's `reviewer_ensemble_verdict` field contains all six per-persona structured critiques plus a meta-review summary with explicit `blockers_remaining` array, OR a documented `REVIEWER_DEFERRED` status with reason.
  - Negative Tests (expected to FAIL):
    - An ensemble run that silently omits a persona's verdict (without `REVIEWER_DEFERRED` status) is rejected by `pipeline/reviewers/validate_ensemble_output.py`.
    - Reviewer outputs that reference a forbidden target name in their text body are flagged by `pipeline/reviewers/scan_reviewer_outputs.py` (non-blocking warning during Phase α; blocker during Phase β where ranking output is also being audited).
    - A round where the recorded backbone-assignment JSON shows all six personas on the same backbone (rather than randomized) is flagged unless explicitly justified by the rate-limit fallback log.

- AC-6: Anti-Bias Validation Suite implements all five mechanisms from draft §6 with target-agnostic thresholds. GDF15-specific verification of these thresholds is performed exclusively by the External Evaluator (AC-7), not by Pipeline-side code.
  - Positive Tests (expected to PASS):
    - `pipeline/anti_bias/run_suite.sh` produces a JSON containing all five mechanism results: LOO ablation (one entry per dimension, reports each dimension's rank-correlation with the full ranking), negative-control ranking distribution (rank of each NC in the universe, expressed as a percentile), literature-blinded re-rank (full re-ranked output with named-entity redaction applied uniformly to all candidates), cross-biobank MR replication (or `{status: "OPTIONAL_SKIPPED", reason: "..."}`), permutation-test empirical p-value distribution.
    - Pipeline-side thresholds in `pipeline/anti_bias/thresholds.json` are TARGET-AGNOSTIC: e.g., "LOO ablation must not change the top-5 ranking by more than K positions on average across dimensions", "negative controls in the bottom HALF of the universe by mean percentile", "permutation-test top-candidate p-value < 0.001". No specific target identifier (GDF15, GFRAL, MIC-1, NAG-1) appears in `thresholds.json` or any Pipeline anti-bias source.
    - GDF15-specific verification (e.g., "GDF15 remains in top 5 under all LOO ablations", "literature-blinded GDF15 in top 25%") is computed by `evaluator/evaluator.py` after Phase β runs; these target-specific checks live in `evaluator/expected_thresholds.json`, not in pipeline-side files.
    - Failures of individual checks are reported (do not silently invalidate) and the meta-review weighs them.
  - Negative Tests (expected to FAIL):
    - Removing any check from the suite causes `pipeline/anti_bias/validate_suite_output.py` to reject the suite output as incomplete.
    - Setting cross-biobank to `OPTIONAL_SKIPPED` without a `reason` string is rejected.
    - `scripts/scan_target_leakage.sh` on `pipeline/anti_bias/` must return zero hits for forbidden target names.

- AC-7: External Evaluator runs Verbose mode only, after the lock tag, and is the sole holder of GDF15-specific verification logic.
  - Positive Tests (expected to PASS):
    - `evaluator/expected_answer.json` exists with the schema in draft §4.2 and is read only by `evaluator/evaluator.py`.
    - `evaluator/expected_thresholds.json` enumerates the target-specific anti-bias verifications (GDF15 top 5 under all LOO, GDF15 in literature-blinded top 25%, etc.) that are NOT permitted to live in Pipeline-side code.
    - `evaluator/evaluator.py --mode verbose --input runs/round_N/output.json --output diagnostics/round_N.md` produces a Markdown diagnostic with full detail: ranking of GDF15, per-dimension contribution, anti-bias check pass/fail against `expected_thresholds.json`, reviewer-ensemble summary, post-hoc platform check result.
    - The Pipeline's source-leakage scanner (AC-2 Negative) verifies no Pipeline code reads `evaluator/expected_answer.json` or `evaluator/expected_thresholds.json`.
  - Negative Tests (expected to FAIL):
    - Any invocation of `evaluator/evaluator.py` before the lock tag exists is rejected by `scripts/loop_orchestrator.sh`.
    - Any Pipeline-side import or open of files in `evaluator/` is rejected by `scripts/scan_target_leakage.sh`.

- AC-8: Loop Orchestration implements round lifecycle, budget caps, rate-limit handling, rollback, and stuck detection per draft §4.7.
  - Positive Tests (expected to PASS):
    - `scripts/loop_orchestrator.sh` honors `MAX_ROUNDS=15` (default; configurable via env var), `MAX_WALLCLOCK_HOURS=8` (configurable), and writes one `proposals/round_N.md`, `runs/round_N/`, `diagnostics/round_N.md`, `reviews/round_N.md` per round.
    - Hitting any rate-limit error from Codex/Gemini/Claude triggers `RATE_LIMITED.md` containing: which API limited, which env var to set (`OPENAI_API_KEY` for Codex, `GEMINI_API_KEY` for Gemini, `ANTHROPIC_API_KEY` for Claude), exact instructions to obtain the key (console.anthropic.com, platform.openai.com, aistudio.google.com/apikey), and how to resume the loop after the env var is set. If the failure is on Codex or Gemini and the *other* LLM backbone is still healthy, the loop continues using the healthy backbone for reviewer-ensemble personas and logs the degradation; if the failure is on Claude (the loop driver itself), the loop halts and the user is expected to switch to API billing per the RATE_LIMITED.md instructions.
    - Three consecutive rounds without improvement on T1–T4 trigger a `STUCK.md` and graceful halt.
    - Rollback restores the pipeline tree to start-of-round state when Codex returns `decision: rollback`.
  - Negative Tests (expected to FAIL):
    - Exceeding `MAX_ROUNDS` does not silently continue; orchestrator emits a final summary and stops.
    - A round that crashes mid-execution counts toward the budget; the orchestrator does not retry the same round indefinitely.

- AC-9: Reproducibility envelope allows a single command to regenerate the final Pipeline output from cached inputs, with a documented canonicalization process for binary-identity comparison.
  - Positive Tests (expected to PASS):
    - `./pipeline/run_pipeline.sh` produces an output JSON whose canonicalized form (via `scripts/canonicalize_output.py`, which strips/normalizes timestamps, removes runtime-dependent fields enumerated in `pipeline/CANONICAL_EXCLUSIONS.md`, sorts JSON keys, and pretty-prints) is byte-identical to the loop's final canonicalized output when run from a clean clone.
    - `pipeline/REQUIREMENTS.txt` (Python) and/or `pipeline/renv.lock` (R) pin all dependencies; running `./pipeline/setup_env.sh` installs them.
    - Dockerfile at `pipeline/Dockerfile` (optional but recommended) builds an image where `run_pipeline.sh` executes successfully.
    - `scripts/preflight.sh` is invoked before the overnight loop starts and verifies: cached data snapshots present, API credentials valid, disk space sufficient, git working tree clean, no uncommitted changes; missing requirements cause preflight to fail before Phase α begins, not mid-loop.
  - Negative Tests (expected to FAIL):
    - Removing the dependency lockfile causes setup to fail with a clear missing-lockfile error.
    - Running `preflight.sh` against an empty `pipeline/data_sources/snapshots/` directory must fail with explicit cache-missing error and abort the overnight loop.

- AC-10: Final Report includes honest reporting per draft Commitment 3, a Methodology Transparency disclosure section, and Cell paper Section 1 figure sketches.
  - Positive Tests (expected to PASS):
    - `FINAL_RESULT.md` exists at loop termination (success OR honest-failure status) and includes: termination status, final ranked top 25, whether GDF15 is in the top 5 and its rank as computed by `evaluator/evaluator.py`, anti-bias check pass/fail summary (target-agnostic Pipeline-side suite + target-aware Evaluator-side verification), reviewer ensemble verdict, post-hoc platform compatibility table for top 5, link to `pipeline/README.md`, and seven figure sketches for Section 1 (Fig 1 architecture overview; Fig 2 candidate universe; Fig 3 per-dim heatmap; Fig 4 composite ranking; Fig 5 anti-bias gauntlet; Fig 6 reviewer ensemble; Fig 7 post-hoc platform check).
    - A `METHODOLOGY_TRANSPARENCY.md` artifact exists as an INTERNAL-ONLY audit record (not for inclusion in the Cell manuscript per resolved DEC-1) and explicitly states: (a) the Loop was developed with GDF15 as the hidden expected answer held by the External Evaluator; (b) Phase α was evaluator-free — the External Evaluator was NOT consulted during methodology design, eliminating the iterative-target-tuning channel; (c) Phase β post-lock changes were limited to engineering concerns and audited by Codex against `LOCKED_ARTIFACTS.json` SHA256 hashes; (d) per the user's manuscript-disclosure decision (DEC-1 = DO NOT DISCLOSE), this artifact remains internal and is not surfaced in the Cell paper.
    - The `evaluator/expected_answer.json` file is listed in `.gitignore` so it does NOT get pushed to a public GitHub remote (in addition to the project's existing no-auto-push rule).
  - Negative Tests (expected to FAIL):
    - If termination is reached only because budget exhausted (not because all T1–T6 pass), the Final Report's status field must read `BUDGET_EXHAUSTED_HONEST_FAILURE` and accurately describe which criteria failed without papering over them. A separate `STUCK.md` may also be written for legacy compatibility with §4.7 of the draft, but `FINAL_RESULT.md` is always written in this case.
    - The Final Report does not silently elevate GDF15 if the locked Pipeline's actual ranking placed it outside the top 5; ranking results in the Final Report must be byte-derived from `evaluator/evaluator.py --mode verbose` output, not human-edited.

- AC-11: Each round of `pipeline/run_pipeline.sh` automatically emits a self-contained, human-readable walkthrough at `runs/round_N/round_N_walkthrough.md` describing exactly what the pipeline did, why, and what it produced — derived verbatim from that round's on-disk artifacts.
  - Positive Tests (expected to PASS):
    - After `bash pipeline/run_pipeline.sh sample_input.json runs/round_N/output.json N` completes successfully, `runs/round_N/round_N_walkthrough.md` exists and is non-empty.
    - The walkthrough contains one section per pipeline step (Steps 1–10 as defined in `pipeline/run_pipeline.sh`), and each section MUST include three labeled subsections in this order: (1) **What it did** — the concrete operation performed plus key input/output file paths; (2) **Why** — the methodological motivation, with a short rationale referencing the relevant AC or plan section; (3) **Results** — the concrete numbers, PASS/FAIL labels, and produced artifact paths derived from that round's artifacts.
    - The walkthrough embeds actual quantitative values from the round (not narrative summaries): top-N candidate composite scores, per-dimension z-scores for the top candidate, anti-bias mechanism actual values vs thresholds with explicit PASS/FAIL labels, permutation empirical p-value, reviewer ensemble status, count of propagated blockers.
    - The walkthrough embeds reviewer-prose excerpts for at least each persona that raised a propagated blocker (truncated to 200 chars), plus that persona's adjudication status from `meta_review.adjudications`. Personas with no propagated blocker are summarized as a one-line "no blocker" entry.
    - The walkthrough is target-blind in the same sense the reviewer dossier is: it MAY reference the ranked candidate by gene symbol when reading `runs/round_N/output.json` (which is post-evaluator and includes the symbol) — explicit Cell-paper figure sketches and reviewer prose remain anonymized via `pipeline/reviewers/scan_reviewer_outputs.py`.
    - `bash scripts/scan_target_leakage.sh pipeline` continues to PASS after the walkthrough generator is added (the generator script must contain zero forbidden gene-symbol literals; it reads candidate symbols only from runtime artifacts).
  - Negative Tests (expected to FAIL):
    - A pipeline run that completes Steps 1–10 but skips walkthrough generation must be detected: the absence of `runs/round_N/round_N_walkthrough.md` after a successful pipeline exit must cause `pipeline/run_pipeline.sh` to exit non-zero.
    - The walkthrough generator must refuse to fabricate data: when an expected artifact (e.g., `runs/round_N/reviewer_ensemble_verdict.json`) is missing, the corresponding walkthrough section must say "ARTIFACT_MISSING: \<path\>" rather than silently producing plausible-sounding prose.

- AC-12: Cell paper Section 1 figures are publication-grade plots produced by an R script, not ASCII/Markdown sketches.
  - Positive Tests (expected to PASS):
    - `figures/Section1/generate_figures.R` exists and, when invoked as `Rscript figures/Section1/generate_figures.R`, produces all seven figures (Fig 1 architecture overview; Fig 2 candidate universe; Fig 3 per-dim heatmap; Fig 4 composite ranking; Fig 5 anti-bias gauntlet; Fig 6 reviewer ensemble; Fig 7 post-hoc platform check) as both PNG (≥300 dpi) and PDF in `figures/Section1/output/`.
    - The R script reads its data from `runs/round_N/output.json`, `runs/round_N/reviewer_ensemble_verdict.json`, `runs/round_N/anti_bias/_results_*.json`, and `runs/round_N/platform_compatibility_top25.tsv` — not from hand-coded values. The round number N is selected by a `--round` CLI argument (default: latest round under `runs/`).
    - Both PNG and PDF outputs are committed to git under `figures/Section1/output/` so anyone cloning the repo immediately sees the manuscript figures without needing to run R locally.
    - `figures/Section1/README.md` exists and lists required R packages and the exact command to regenerate.
    - The old ASCII/Markdown figure sketches at `figures/Section1/Fig*.md` are removed (AC-12 supersedes the AC-10 sketch requirement; the `FINAL_RESULT.md` figure-reference section is updated to point at PNG/PDF instead).
  - Negative Tests (expected to FAIL):
    - If `generate_figures.R` cannot find required R packages, it must exit non-zero with a clear "missing-package" error rather than producing partial output.
    - If a referenced run directory (e.g., `runs/round_N/`) is missing required artifacts, the script must skip the affected figure and emit a clear stderr warning rather than producing a misleading plot.

## Path Boundaries

### Upper Bound (Maximum Acceptable Scope)

The implementation includes a fully functional two-phase Loop with: a real candidate universe of 800–1500 protein-coding genes constructed from Open Targets + GWAS Catalog + ChEMBL + curated literature snapshots; 6–10 scoring dimensions backed by independent data modalities; a six-persona Cell-reviewer ensemble with at least two distinct LLM backbones; all five anti-bias mechanisms operational (cross-biobank MR may use a single biobank if multi-biobank access is infeasible overnight, documented as `OPTIONAL_PARTIAL`); a Dockerized reproducibility envelope; complete `FINAL_RESULT.md` with all seven figure sketches as text/pseudo-Mermaid plus quantitative data; methodology lock SHA published in `PRE_REGISTRATION.md` and additionally hashed to an outbound text channel if internet is available.

### Lower Bound (Minimum Acceptable Scope)

The implementation includes a minimal but runnable two-phase Loop with: a candidate universe of at least 200 protein-coding genes constructed from at least Open Targets and a single GWAS source; at least 5 scoring dimensions; a six-persona ensemble using a single LLM backbone (with logged warning); at least 4 of 5 anti-bias mechanisms operational (cross-biobank MR may be `OPTIONAL_SKIPPED`); a non-Dockerized reproducibility envelope based on `pip install -r requirements.txt`; a `FINAL_RESULT.md` summarizing what was achieved and what was not (e.g., "Phase β reached only 2 engineering rounds before budget exhaustion"); methodology lock SHA in `PRE_REGISTRATION.md`.

### Allowed Choices

- Can use: Python 3.11+, R 4.x for biobank/MR analyses if executed, Jupyter notebooks for exploratory figures, JSON for all structured IO, Markdown for human-readable artifacts, Codex CLI (`/humanize:ask-codex`) and Gemini CLI (`/humanize:ask-gemini`) for LLM calls, git tags for lock points, Docker (optional), GitHub Actions config files (optional), any open-source python/R package as long as it is pinned.
- Cannot use: any data source requiring private credentials beyond what the user has already set up; any LLM provider not invoked via the humanize wrapper scripts; any code path that imports `evaluator/expected_answer.json` from outside `evaluator/`; hard-coded references to specific gene symbols including but not limited to GDF15, GFRAL, MIC-1, NAG-1 in any Pipeline-side file; auto-push to GitHub remote (per project preference, only local commits); silent fallback to weaker LLM models on rate-limit (must surface `RATE_LIMITED.md`).

## Feasibility Hints and Suggestions

### Conceptual Approach

```
project-root/
├── draft.md                                # immutable spec (already exists)
├── plan.md                                 # this document
├── evaluator/
│   ├── expected_answer.json                # GDF15 ground truth (only read by evaluator)
│   └── evaluator.py                        # --mode blind | --mode verbose
├── pipeline/
│   ├── PRE_REGISTRATION.md                 # locked methodology manifest + git SHA
│   ├── run_pipeline.sh                     # single-command reproducibility
│   ├── setup_env.sh
│   ├── Dockerfile                          # optional
│   ├── REQUIREMENTS.txt                    # Python pins
│   ├── renv.lock                           # optional R pins
│   ├── README.md
│   ├── universe/
│   │   ├── build_universe.py
│   │   └── candidate_universe.tsv          # built artifact
│   ├── scoring/
│   │   ├── dimensions.json
│   │   ├── weights.json
│   │   ├── validate_weights.py
│   │   └── score_*.py                      # one per dimension
│   ├── reviewers/
│   │   ├── config.json
│   │   ├── R1_molecular_biologist.md
│   │   ├── R2_clinical_translator.md
│   │   ├── R3_geneticist_biostatistician.md
│   │   ├── R4_pharmacologist.md
│   │   ├── R5_ai_methods_reviewer.md
│   │   ├── R6_editor.md
│   │   ├── meta_review.md
│   │   ├── run_ensemble.sh
│   │   └── validate_ensemble_output.py
│   ├── anti_bias/
│   │   ├── thresholds.json
│   │   ├── run_suite.sh
│   │   ├── loo_ablation.py
│   │   ├── negative_controls.py
│   │   ├── literature_blinded.py
│   │   ├── cross_biobank_mr.py
│   │   ├── permutation_test.py
│   │   └── validate_suite_output.py
│   ├── data_sources/
│   │   ├── MANIFEST.md
│   │   └── snapshots/                      # cached Open Targets, GWAS, ChEMBL, etc.
│   └── post_hoc/
│       └── platform_compatibility.py
├── scripts/
│   ├── loop_orchestrator.sh
│   ├── round_proposal.sh
│   ├── round_implement.sh
│   ├── round_run.sh
│   ├── round_evaluate.sh
│   ├── round_review.sh
│   ├── round_decide.sh
│   ├── round_commit.sh
│   ├── verify_methodology_lock.sh
│   └── scan_target_leakage.sh
├── proposals/round_*.md
├── runs/round_*/output.json
├── diagnostics/round_*.md
├── reviews/round_*.md
├── LOOP_SUMMARY.md
├── FINAL_RESULT.md                         # or STUCK.md
└── METHODOLOGY_TRANSPARENCY.md
```

Conceptual loop flow:

```
PHASE α (target-blind methodology design):
  Round 0: bootstrap skeleton (skeleton Pipeline + cached data + Codex methodology critique)
  Round 1..N1: methodology iteration
    - Claude proposes methodology changes
    - Codex critiques (must NOT see Evaluator diagnostic, only methodology rationale)
    - Pipeline does NOT run on the External Evaluator in this phase
    - Pipeline MAY run on a small validation sub-universe (e.g., 50 candidates) for engineering sanity, with Blind Evaluator only
  When Codex declares methodology converged → create git tag v1.0-methodology-locked
  Write PRE_REGISTRATION.md with the locked manifest

PHASE β (post-lock engineering):
  Round N1+1..MAX: engineering iteration
    - Pipeline runs end-to-end on full universe
    - Verbose Evaluator returns rich diagnostic
    - Claude proposes ONLY engineering fixes (bugs, schema, missing-data handling, performance)
    - Codex audits diffs for forbidden-change patterns (any modification to locked files → reject)
    - When T1–T6 all pass, terminate
    - If budget exhausted, write FINAL_RESULT.md or STUCK.md honestly
```

### Relevant References

- `draft.md` — immutable specification this plan implements
- `references/Ghareeb-2026.pdf` — Robin multi-agent system (FutureHouse) for architecture inspiration (Crow/Falcon/Finch pattern)
- `references/Gottweis-2026.pdf` — Google Co-Scientist (multi-agent tournament evolution) for reviewer ensemble inspiration
- `references/dongdong-2023.pdf` — GDF15 muscle thermogenesis paper, includes 2SMR template using UKBB GWAS data
- `references/mullican-2017.pdf` — GFRAL receptor discovery, GDF15 biology baseline
- `references/kaiyue-2026.pdf` — Cheng Lab saRNA-Nppa platform paper (the foundation for delivery)
- `/Users/yliu/.claude/projects/-Users-yliu-Desktop-Columbia---Biostatistics-Cheng-Lab-GDF15/memory/` — project memories: rate-limit → prompt API key (apply to AC-8); docs in English; pipeline objectivity boundary test

## Dependencies and Sequence

### Milestones

1. Milestone 1 — Bootstrap and Environment.
   - Phase A: Provision `pipeline/`, `evaluator/`, `scripts/` skeletons and `expected_answer.json`.
   - Phase B: Cache initial data snapshots (Open Targets associations for obesity/T2D/MASH, GWAS Catalog summary indices, ChEMBL metabolic targets) into `pipeline/data_sources/snapshots/`. Document in `MANIFEST.md`.
   - Phase C: Stand up `scripts/loop_orchestrator.sh` and verify it can execute one no-op round end-to-end.

2. Milestone 2 — Phase α Methodology Design (Blind Evaluator).
   - Phase A: Implement v0 of `pipeline/universe/build_universe.py` and `pipeline/scoring/dimensions.json` with 5 starter dimensions.
   - Phase B: Implement v0 of six reviewer prompts and `pipeline/reviewers/run_ensemble.sh`.
   - Phase C: Implement v0 of all five anti-bias mechanisms with `OPTIONAL_SKIPPED` allowed for cross-biobank.
   - Phase D: Implement `evaluator/evaluator.py` with `--mode blind` only (verbose mode is stubbed until lock).
   - Phase E: Codex iterates methodology with Claude until convergence on rubrics, thresholds, and dimension definitions.
   - Phase F: `git tag v1.0-methodology-locked`; write `pipeline/PRE_REGISTRATION.md`.

3. Milestone 3 — Phase β Engineering Iteration (Verbose Evaluator).
   - Phase A: Enable `--mode verbose` in evaluator.
   - Phase B: Run Pipeline end-to-end on full candidate universe.
   - Phase C: Iterate ONLY on engineering issues (bug fixes, schema validation, missing-data graceful handling, performance).
   - Phase D: When T1–T6 pass OR budget exhausts, write `FINAL_RESULT.md` (success) or `STUCK.md` (timeout).
   - Phase E: Write `METHODOLOGY_TRANSPARENCY.md`; commit final state.

4. Milestone 4 — Reproducibility Validation.
   - Phase A: Run `./pipeline/run_pipeline.sh` from a clean clone scenario (use a separate working directory) to confirm reproducibility.
   - Phase B: Verify all artifacts are present and well-formed.

Relative dependencies: Milestone 1 must complete before Milestones 2–4. Milestone 2's Phase F (lock) must complete before Milestone 3 may begin. Milestone 4 may begin once Milestone 3 has produced any successful Pipeline output.

## Task Breakdown

| Task ID | Description | Target AC | Tag | Depends On |
|---------|-------------|-----------|-----|------------|
| task1 | Provision project skeleton: `pipeline/`, `evaluator/`, `scripts/` directories; create empty `expected_answer.json` with schema | AC-1, AC-7 | coding | - |
| task2 | Implement `scripts/scan_target_leakage.sh` (greps Pipeline source for forbidden symbols, returns non-zero on hit) | AC-2 | coding | task1 |
| task3 | Implement `scripts/verify_methodology_lock.sh` (checks git tag exists, compares current vs locked manifest) | AC-1 | coding | task1 |
| task4 | Cache initial data snapshots from Open Targets, GWAS Catalog, ChEMBL; write `pipeline/data_sources/MANIFEST.md` | AC-2.1, AC-3 | coding | task1 |
| task5 | Implement `pipeline/universe/build_universe.py` and produce `candidate_universe.tsv` with documented inclusion rules | AC-3 | coding | task4 |
| task6 | Specify `pipeline/scoring/dimensions.json` (5 starter dimensions) and `weights.json`; implement `validate_weights.py` | AC-4 | coding | task5 |
| task7 | Implement per-dimension scoring scripts under `pipeline/scoring/score_*.py` | AC-4 | coding | task6 |
| task8 | Author six reviewer persona prompts under `pipeline/reviewers/R*.md` and the `meta_review.md` aggregator | AC-5 | coding | task1 |
| task9 | Implement `pipeline/reviewers/run_ensemble.sh` and `validate_ensemble_output.py` with at least 2 LLM backbones | AC-5 | coding | task8 |
| task10 | Implement all five anti-bias mechanisms under `pipeline/anti_bias/`, plus `thresholds.json` and `validate_suite_output.py` | AC-6 | coding | task7 |
| task11 | Implement `evaluator/evaluator.py` with `--mode blind` and `--mode verbose`; enforce mode gating on lock tag | AC-1.1, AC-1.2, AC-7 | coding | task1 |
| task12 | Implement `pipeline/run_pipeline.sh` orchestrating universe → scoring → ensemble → anti-bias → post-hoc; produce IO-contract-compliant output JSON | AC-2 | coding | task5,task7,task9,task10 |
| task13 | Implement `pipeline/post_hoc/platform_compatibility.py` consuming Top N from the output JSON | AC-2, AC-10 | coding | task12 |
| task14 | Implement `scripts/loop_orchestrator.sh` with round lifecycle, budget caps, rate-limit handling (writes `RATE_LIMITED.md`), rollback, stuck detection | AC-8 | coding | task11 |
| task15 | Implement `scripts/preflight.sh` and run before any Phase α work; verify cache snapshots, API credentials, git state, disk | AC-9 | coding | task4,task14 |
| task16 | Implement `scripts/canonicalize_output.py` and `pipeline/CANONICAL_EXCLUSIONS.md` | AC-9 | coding | task12 |
| task17 | Run Phase α methodology iteration rounds via orchestrator (evaluator-free); convergence judged by Codex + reviewer-ensemble dry-run on 50-target validation universe + leakage scans | AC-1, AC-1.1, AC-4, AC-5, AC-6 | coding | task15 |
| task18 | Codex methodology-rigor pre-lock audit (one shot, before lock) | AC-1, AC-1.3 | analyze | task17 |
| task19 | Build `pipeline/LOCKED_ARTIFACTS.json` with path/purpose/SHA256/mutability for every locked artifact | AC-1.3 | coding | task18 |
| task20 | Execute methodology lock: `git tag v1.0-methodology-locked`; write `pipeline/PRE_REGISTRATION.md`; verify lock via `verify_methodology_lock.sh` | AC-1, AC-1.3, AC-2 | coding | task19 |
| task21 | Run Phase β (Verbose Evaluator engineering iteration) using the orchestrator | AC-1.2, AC-2, AC-7, AC-8 | coding | task20 |
| task22 | Codex per-round forbidden-change audit during Phase β (SHA256 verification + diff-pattern checks; requires engineering_audit_note for ranking-altering changes) | AC-1, AC-1.2 | analyze | task21 |
| task23 | Create `pipeline/REQUIREMENTS.txt`, `pipeline/setup_env.sh`, and optional `pipeline/Dockerfile` | AC-9 | coding | task12 |
| task24 | Validate reproducibility: re-run `./pipeline/run_pipeline.sh` from a clean working directory; compare canonicalized outputs | AC-9 | coding | task23,task16 |
| task25 | Write `FINAL_RESULT.md` with rankings, anti-bias summary, post-hoc platform table, figure sketches; honest-failure status if T1–T6 not all met | AC-10 | coding | task21 |
| task26 | Write `METHODOLOGY_TRANSPARENCY.md` describing Phase α/β separation, evaluator-free Phase α, hash-based lock, and disclosure-decision flag | AC-10 | coding | task25 |
| task27 | Generate seven figure sketches (Fig 1–Fig 7 per draft §10) as Markdown/Mermaid + quantitative data tables | AC-10 | coding | task25 |
| task28 | Final integrity audit: run `scan_target_leakage.sh` + `verify_methodology_lock.sh` + AC validation suite; document any unmet AC in `FINAL_RESULT.md` | AC-1..AC-10 | analyze | task25,task26,task27 |
| task29 | Implement `pipeline/generate_round_walkthrough.py` (reads all artifacts in `runs/round_N/` plus `diagnostics/round_N.md` and per-round audit note; emits self-contained `runs/round_N/round_N_walkthrough.md` with one section per pipeline step containing What/Why/Results subsections, embedded numbers, and reviewer-prose excerpts per AC-11); wire into `pipeline/run_pipeline.sh` as Step 11; pipeline exits non-zero if walkthrough is missing after Steps 1-10 succeed | AC-11 | coding | task12 |
| task30 | Implement `figures/Section1/generate_figures.R` producing Fig 1-Fig 7 as both PNG (≥300 dpi) and PDF in `figures/Section1/output/` from `runs/round_N/` artifacts (--round CLI arg, default latest); write `figures/Section1/README.md` listing R-package dependencies (ggplot2, scales, cowplot, DiagrammeR or equivalent) and run command; delete the legacy ASCII/Markdown sketches at `figures/Section1/Fig*.md`; update FINAL_RESULT.md figure references from `.md` to `.pdf`/`.png` | AC-12 | coding | task25 |
| task31 | R12+ re-lock and tag move after AC-11/AC-12 land: refresh LOCKED_ARTIFACTS for changed artifacts (run_pipeline.sh + new generate_round_walkthrough.py); write per-round engineering audit note; force-move v1.0-methodology-locked to the close-out commit; regenerate runs/round_N and verify pre_registration_hash equals current tag SHA | AC-1, AC-10, AC-11, AC-12 | coding | task29,task30 |

## Claude-Codex Deliberation

### Agreements
- The draft accurately captures intent: design + run an autonomous loop that produces a Cell-grade pipeline whose ranked output puts GDF15 in the top tier.
- Six-persona reviewer ensemble lives in the Inner Pipeline (per draft v1.1 clarification); separate Codex review in the Loop is a methodological integrity check.
- Anti-bias mechanisms must all run, with failures reported (not silently invalidated).
- The user's project memory (rate limit → prompt API key, no auto-push, English docs) is binding.

### Resolved Disagreements
- **Architecture: single-phase iterative loop vs. two-phase (methodology-design / engineering-only post-lock).** Codex flagged that iterative methodology improvement guided by a GDF15-aware evaluator constitutes indirect target-rigging even with the boundary test. Resolution: adopt the two-phase architecture. (First Codex round.)
- **Phase α evaluator policy.** Second Codex round flagged that even Blind Evaluator pass/fail signal becomes a target-tuning signal over repeated rounds. Resolution: Phase α is now FULLY evaluator-free; convergence is judged by Codex methodological critique + reviewer-ensemble dry-run on a generic 50-target validation universe + leakage/schema scans. The External Evaluator is only invoked after the lock tag exists.
- **Anti-bias threshold location.** Second Codex round flagged that `pipeline/anti_bias/thresholds.json` containing "GDF15 in top 5" leaks the target. Resolution: all GDF15-specific thresholds moved to `evaluator/expected_thresholds.json`. Pipeline-side `thresholds.json` contains only target-agnostic criteria (LOO stability metrics, negative-control percentile rules, permutation p-value thresholds for the top-ranked target whoever it is).
- **AC-3 universe test target-awareness.** Second Codex round flagged that checking GDF15 presence in the universe is a target-aware Pipeline-side check. Resolution: rewrote AC-3 to test therapeutic-class diversity (target-agnostic); GDF15 universe-presence verification moved to evaluator-side.
- **Methodology lock mechanism.** Second Codex round flagged that diff-pattern checks alone are insufficient. Resolution: `pipeline/LOCKED_ARTIFACTS.json` lists every locked artifact with SHA256 hash and mutability category (`forbidden` vs `audit_required`); `scripts/verify_methodology_lock.sh` performs hash-based verification.
- **Phase β rank-altering changes.** Second Codex round flagged that "missing-data handling" can disguise scoring changes. Resolution: any Phase β change that materially alters ranking output requires an `engineering_audit_note.md` explaining the bug and why the fix is non-substantive; Codex must endorse the note.
- **AC-10 transparency wording.** Second Codex round flagged that "Phase α calibration used GDF15" contradicted the methodological defense. Resolution: rewrote to state explicitly that Phase α was evaluator-free, eliminating the iterative-target-tuning channel.
- **Preflight cache audit.** Second Codex round recommended verifying caches before the overnight loop starts. Resolution: added `scripts/preflight.sh` as a hard precondition (task15).
- **Reviewer ensemble rate-limit fallback.** Second Codex round noted ensemble fragility under rate limits. Resolution: AC-5 now includes graceful degradation: single-backbone → cached → deferred.
- **AC-9 reproducibility byte-identity.** Second Codex round flagged "byte-identical modulo timestamps" as brittle. Resolution: defined via `scripts/canonicalize_output.py` + `pipeline/CANONICAL_EXCLUSIONS.md`.
- **Negative-control acceptance threshold: bottom quartile vs bottom half.** First Codex round flagged "bottom quartile" as brittle. Resolution: relaxed to "bottom half" in `anti_bias/thresholds.json`; original quartile documented as the aspirational level.
- **Cross-biobank MR requirement: mandatory vs optional.** First Codex round flagged that multi-biobank MR overnight is high-risk for completion. Resolution: documented OPTIONAL component; `{status: "OPTIONAL_SKIPPED", reason: "..."}` is acceptable.
- **Live API access vs cached-only data.** First Codex round flagged feasibility risk. Resolution: Phase α uses ONLY cached snapshots + LLM calls. Live data API calls are reserved for Phase β if explicitly needed.

### Convergence Status
- Final Status: `converged` — after two Codex passes, all REQUIRED_CHANGES have been addressed:
  - Phase α made evaluator-free (no Blind Evaluator iteration); convergence judged by Codex methodological critique + reviewer-ensemble dry-run on a generic 50-target validation sub-universe + leakage/schema scans.
  - All GDF15-specific anti-bias thresholds moved from Pipeline-side `anti_bias/thresholds.json` to Evaluator-side `evaluator/expected_thresholds.json`. Pipeline-side thresholds are target-agnostic.
  - AC-3 universe-builder test rewritten to be target-agnostic (therapeutic-class diversity check); GDF15 universe-presence verification moved to evaluator-side.
  - Methodology lock made hash-based via `LOCKED_ARTIFACTS.json` (SHA256 per artifact) and `verify_methodology_lock.sh`.
  - Phase β rank-altering changes require an `engineering_audit_note.md` that Codex must endorse.
  - Preflight cache audit (`scripts/preflight.sh`) added before overnight loop start.
  - Reviewer ensemble has graceful rate-limit degradation (single backbone → cached outputs → deferred status).
  - `AC-9` canonicalization defined via `scripts/canonicalize_output.py` + `pipeline/CANONICAL_EXCLUSIONS.md`.
  - `AC-10` transparency wording corrected (Phase α was evaluator-free, not "calibrated against" GDF15).
  - Task list expanded from 25 to 28 to cover preflight, canonicalizer, and hash-based lock-manifest creation.
  - All 6 `Pending User Decisions` (DEC-1..DEC-6) remain `PENDING` for explicit user input before loop launch (their substance has been refined based on Codex feedback).

## Pending User Decisions

All six items resolved by user before launch.

- DEC-1: Final paper disclosure of evaluator-based development.
  - Decision: **DO NOT DISCLOSE** in the Cell manuscript. `METHODOLOGY_TRANSPARENCY.md` is produced as an internal-only audit artifact and is excluded from the manuscript narrative. `evaluator/expected_answer.json` is gitignored to prevent accidental public push.
  - Decision Status: RESOLVED — User decision overrides both Claude's and Codex's preference to disclose; user accepts the credibility tradeoff.

- DEC-2: Budget priority between locked methodology vs partial Phase β.
  - Decision: **Trust subscriptions; rely on API-key fallback on rate-limit.** Loop runs normally Phase α → lock → Phase β. On rate limit, write `RATE_LIMITED.md` with API-key setup instructions; user manually switches to API billing in the morning to resume if needed.
  - Decision Status: RESOLVED — equivalent to choice (c) "trust subscriptions + API key safety net".

- DEC-3: Cached-only data vs live API calls.
  - Decision: **Allow live API calls in both Phase α and Phase β.** All non-LLM live calls are logged to `runs/round_N/api_calls.log` for audit. Cache-first preferred for cost and reproducibility; live fallback when cache misses.
  - Decision Status: RESOLVED.

- DEC-4: Reviewer ensemble backbone assignment.
  - Decision: **Randomized per round.** Each round, each persona is randomly assigned to Codex or Gemini with uniform probability; assignment recorded to `runs/round_N/reviewer_backbone_assignment.json`. A deterministic seed derived from round number enables replay.
  - Decision Status: RESOLVED.

- DEC-5: Cost caps per round.
  - Decision: **Soft cap $20/round (logged), hard cap $100/round (triggers STUCK.md).** Accepted.
  - Decision Status: RESOLVED.

- DEC-6: LLM-scored dimensions in the methodology.
  - Decision: **Allowed**, with three safeguards: (1) deterministic seed where the LLM API supports it (or rule-based reseed of inputs); (2) cached LLM transcripts keyed by prompt-hash + input-hash; (3) a rule-based fallback scorer for the same dimension that runs when LLM is unavailable.
  - Decision Status: RESOLVED.

## Implementation Notes

### Code Style Requirements
- Implementation code and comments must NOT contain plan-specific terminology such as "AC-", "Milestone", "Step", "Phase", or similar workflow markers in the codebase. The Phase α/β nomenclature appears in `LOOP_SUMMARY.md`, `PRE_REGISTRATION.md`, and `METHODOLOGY_TRANSPARENCY.md` documents but should NOT appear inside Python/R/shell scripts that comprise the Pipeline itself.
- All Pipeline-side source files, comments, commit messages, and documentation use descriptive, domain-appropriate naming (e.g., `score_genetic_causal.py`, `build_candidate_universe.py`, `verify_methodology_lock.sh`).
- Per project memory: all written artifacts (drafts, plans, code comments, READMEs, commit messages) in English; conversational replies to the user may remain in Chinese.
- Per project memory: never auto-push to git remote; only local commits. Per-round git commits are required by AC-8; pushing is the user's manual action.
- Per project memory: on any rate-limit (Codex/Gemini/Claude), the Loop pauses and writes `RATE_LIMITED.md` indicating the corresponding `*_API_KEY` env var to switch to API billing.
- Numeric thresholds in `thresholds.json` and `weights.json` are HARD constraints in the methodology-lock contract; changing them post-lock is detected by `verify_methodology_lock.sh` and rejected.

### Quantitative Metric Treatment (placeholder pending user confirmation)
- GDF15 "in top 5" is treated as a hard verification of the locked Pipeline's correctness, not as an optimization target after lock.
- Negative-control "in bottom half" is treated as a soft constraint (failure flagged in `anti_bias` output but does not invalidate the Pipeline).
- Permutation p < 0.001 is treated as a soft constraint (failure flagged, not invalidating).
- LOO ablation "GDF15 in top 5 under every removal" is treated as a soft constraint at the lower-bound scope (some LOO failures permitted with documentation) and as a hard constraint at the upper-bound scope.

## Output File Convention

This template is used to produce the main output file (e.g., `plan.md`).

### Translated Language Variant

When `alternative_plan_language` resolves to a supported language name through merged config loading, a translated variant of the output file is also written after the main file. Humanize loads config from merged layers in this order: default config, optional user config, then optional project config; `alternative_plan_language` may be set at any of those layers. The variant filename is constructed by inserting `_<code>` (the ISO 639-1 code from the built-in mapping table) immediately before the file extension:

- `plan.md` becomes `plan_<code>.md` (e.g. `plan_zh.md` for Chinese, `plan_ko.md` for Korean)
- `docs/my-plan.md` becomes `docs/my-plan_<code>.md`
- `output` (no extension) becomes `output_<code>`

The translated variant file contains a full translation of the main plan file's current content in the configured language. All identifiers (`AC-*`, task IDs, file paths, API names, command flags) remain unchanged, as they are language-neutral.

When `alternative_plan_language` is empty, absent, set to `"English"`, or set to an unsupported language, no translated variant is written. Humanize does not auto-create `.humanize/config.json` when no project config file is present.

--- Original Design Draft Start ---

# Autonomous Loop Specification: Designing an AI Discovery Pipeline that Rediscovers GDF15

**Status:** Draft v1.1 — input for `/humanize:gen-plan` → `/humanize:start-rlcr-loop`
**Authors:** Cheng Lab, Columbia University
**Target venue:** Cell (main journal)
**Last updated:** 2026-05-27

---

## 0. Abstract (paper-level, what the final result must support)

Tirzepatide and other GLP-1/GIP agonists have transformed obesity treatment but require weekly subcutaneous injections, lose efficacy after discontinuation, and erode lean mass — limitations that constrain long-term adherence and the quality of weight loss. To identify a protein target capable of resolving these limitations simultaneously, we built a pre-registered AI discovery pipeline that scored ~1,200 candidates across a structured set of orthogonal evidence dimensions, with a six-persona simulated-reviewer ensemble providing in-pipeline adversarial critique. Growth differentiation factor 15 (GDF15) ranked first — a hindbrain-acting cytokine whose multi-axis metabolic profile has long been recognized but whose 2-hour plasma half-life made recombinant-protein development clinically impractical. To revive this orphaned target, we encoded GDF15 in a self-amplifying RNA (saRNA) delivered through a sublingual microneedle patch worn for 10 minutes once daily — an at-home, needle-free administration that converts oral mucosa into a self-renewing GDF15 source and is operationally simpler than the weekly injections that define current standard of care. Across three mouse models of obesity-associated MASH, this intervention recapitulated the AI-predicted profile: durable, dose-dependent fat-mass reduction with preserved lean mass, improved insulin sensitivity, and reversal of hepatic steatosis. By coupling adversarially-validated AI target rediscovery with a delivery platform that is both more practical than current injectables and capable of resurrecting pharmacokinetically intractable targets, this work establishes a generalizable framework for next-generation metabolic therapeutics.

---

## 1. What This Document Is

This document specifies a **two-layer autonomous system** that will be implemented and executed via `/humanize:start-rlcr-loop`:

- **Inner layer — the AI Discovery Pipeline.** A program that takes a research question ("find a better weight-loss drug than Tirzepatide") and produces a ranked list of protein targets, recommended delivery modalities, and predicted phenotypic profiles. The pipeline does not know which target the wet lab has validated.
- **Outer layer — the Design Loop.** A meta-process that iteratively improves the Pipeline by: proposing changes → implementing them → running the Pipeline → evaluating the output against ground truth and against methodological-rigor criteria → reviewing whether the changes were principled → iterating until termination.

The user will sleep while the loop runs. The user reviews the final state in the morning.

The expected end state: a Cell-grade AI discovery Pipeline whose ranked output puts GDF15 in the top-tier candidates, supported by independently verifiable evidence dimensions, robust to ablation, and accompanied by a six-persona simulated peer review that endorses the methodology.

---

## 2. Project Context

The Cheng Lab recently published a self-amplifying RNA-LNP platform (Zhang et al., *Science* 2026, doi:10.1126/science.adu9394) for cardiac repair via *Nppa*-encoded pro-ANP. We have separately completed unpublished mouse work adapting this platform to a new target (GDF15), a new delivery route (sublingual microneedles), and a new indication (obesity + insulin resistance + MASH). The wet-lab data shows efficacy with a body-composition profile favorable on lean-mass preservation.

The Cell paper has two halves:

- **Section 1 — AI-driven target rediscovery.** The Pipeline that this loop will produce.
- **Section 2+ — Platform application.** The wet-lab demonstration (already complete).

The narrative is: **AI identified GDF15 as the optimal target; the Cheng Lab platform happens to be ideally suited to deliver it.**

---

## 3. The Inner Layer: AI Discovery Pipeline Specification

### 3.1 IO Contract

**Input.** A structured research question:

```json
{
  "question": "Find a better weight-loss drug than Tirzepatide.",
  "phenotype_profile_desired": {
    "fat_mass_reduction": "high",
    "lean_mass_preservation": "high",
    "glycemic_control": "high",
    "hepatic_steatosis_reduction": "high",
    "durability_after_discontinuation_or_with_infrequent_dosing": "high",
    "patient_administration_burden": "low"
  },
  "indication_context": "adults with co-existing obesity, type 2 diabetes (or prediabetes/insulin resistance), and MASH/NAFLD"
}
```

**Output.** A structured ranking:

```json
{
  "ranked_targets": [
    {
      "rank": 1,
      "target_symbol": "...",
      "ensembl_gene_id": "...",
      "composite_score": 0.0,
      "per_dimension_scores": { "...": 0.0 },
      "predicted_phenotype_profile": { "...": "..." },
      "recommended_delivery_modality": "...",
      "rationale_summary": "..."
    }
    // ... at least top 25 candidates
  ],
  "anti_bias_validation": {
    "loo_ablation": "...",
    "negative_controls": "...",
    "literature_blinded_rerank": "...",
    "permutation_test_p_value": 0.0
  },
  "reviewer_ensemble_verdict": {
    "R1_molecular_biologist": "...",
    "R2_clinical_translator": "...",
    "R3_geneticist_biostatistician": "...",
    "R4_pharmacologist": "...",
    "R5_ai_methods_reviewer": "...",
    "R6_editor": "...",
    "meta_review": "...",
    "blockers_remaining": []
  },
  "pre_registration_hash": "git-sha",
  "reproducibility": "command to reproduce all results"
}
```

### 3.2 Hard Constraints on the Pipeline

These constraints are non-negotiable. The loop's Codex reviewer must enforce them every round.

- **C1 — No leakage of the expected answer.** The Pipeline does not read `evaluator/expected_answer.json` and does not contain any hard-coded reference to GDF15 as a target of interest. Its only knowledge of GDF15 is what arrives through generic data sources (Open Targets, GWAS, literature, etc.) applied uniformly to all candidates.
- **C2 — Candidate universe constructed by inclusive rules.** ~500–1500 protein-coding genes, sourced via documented inclusion rules over Open Targets / GWAS catalogs / clinical-pipeline databases / literature. The universe is not filtered by platform deliverability at scoring time.
- **C3 — Multi-dimensional scoring.** At least 5 orthogonal scoring dimensions, each backed by independent data modalities. The Pipeline itself decides the exact count and naming. No single dimension may dominate the final composite by construction (no dimension weight > 0.4).
- **C4 — Six-persona reviewer ensemble (Inner Pipeline component).** The Pipeline itself instantiates the persona ensemble described in §5.3 as part of its scoring and reporting. The reviewers operate inside the Pipeline, evaluate the scientific soundness of the candidate ranking, and surface their critiques in the Pipeline's output JSON. This is a scientific peer-review function. (Note: this is distinct from the Loop's Codex review in §4.3 Step 6, which is a methodological integrity check on each round's proposed changes, not a science review.)
- **C5 — Anti-bias checks.** All five anti-bias mechanisms (§6) must run and report. Failure of any single check is reported but does not silently invalidate the ranking.
- **C6 — Reproducibility.** Single command runs the full pipeline from raw data sources to final output. Methodology is locked via git hash before final run.
- **C7 — Honest reporting.** If GDF15 (or any specific target) does not rank where expected, the Pipeline reports the actual ranking. Tuning the Pipeline post-hoc to elevate any specific target is forbidden (enforced by the loop's Codex review, see §4.5).

### 3.3 Platform-Compatibility Post-Hoc Check

After the Pipeline produces its ranked list, a separate (clearly labeled) post-hoc evaluation checks the top N candidates against the saRNA + sublingual microneedle delivery platform's hard constraints (secreted protein, ORF ≤ ~15 kb, no complex PTM, active form from circulation). This evaluation does not modify the ranking. It is reported as a separate analysis in the output JSON.

---

## 4. The Outer Layer: The Design Loop

### 4.1 Goal

Iteratively design, run, evaluate, and improve the Inner Pipeline until **all termination criteria (§4.6)** are met, or the budget is exhausted.

### 4.2 The External Evaluator

A program separate from the Pipeline, owned by the loop layer. The Evaluator:

- Has access to `evaluator/expected_answer.json`, which specifies the ground-truth answer:
  ```json
  {
    "expected_top_targets": ["GDF15"],
    "expected_delivery_modality": "self-amplifying RNA via sublingual microneedle patch",
    "rationale_visible_to_evaluator_only": "Cheng Lab wet-lab data validates GDF15 + saRNA + microneedles in three mouse models of MASH-associated obesity (unpublished). The Pipeline must rediscover this answer from public data alone."
  }
  ```
- Compares the Pipeline's output (§3.1) against the expected answer.
- Compares the Pipeline's anti-bias check results against thresholds.
- Compares the reviewer ensemble's verdicts.
- Produces a structured diagnostic report (`diagnostics/round_N.md`):
  - Is GDF15 in the top 5? (if no, by how much is it missed)
  - Which evidence dimensions support / weaken GDF15's ranking
  - Which anti-bias checks pass / fail
  - Which reviewer personas flagged blocker-level concerns
  - Specific suggestions for what the Pipeline could improve **methodologically** (not in a target-specific way)

### 4.3 The Loop Workflow Per Round

```
Round N (N = 1, 2, ..., MAX_ROUNDS):

  Step 1 — READ STATE
    Load pipeline/ (current Pipeline implementation)
    Load all prior diagnostics/ and reviews/
    Load draft.md (this document) as immutable spec

  Step 2 — PROPOSE
    Claude proposes changes to the Pipeline, with justification.
    Justification must pass the boundary test (§5.2): "Would I make this
    change if it hurt GDF15's rank?"
    The proposal is written to proposals/round_N.md before any code change.

  Step 3 — IMPLEMENT
    Claude writes/edits files in pipeline/ to enact the proposal.
    All edits must keep the Pipeline runnable end-to-end.

  Step 4 — RUN
    Execute the Pipeline on the input (§3.1) using a single canonical command.
    Capture full output to runs/round_N/output.json.
    Capture stderr, run time, and any errors to runs/round_N/log.txt.

  Step 5 — EVALUATE
    Run the External Evaluator on runs/round_N/output.json.
    Evaluator writes diagnostics/round_N.md.

  Step 6 — REVIEW  (Outer Loop — methodological integrity check, NOT a science review)
    Note: this Codex review is the Loop's own integrity check. It is distinct
    from the Inner Pipeline's 6-persona reviewer ensemble (§5.3), which evaluates
    the scientific soundness of the ranking and runs inside the Pipeline itself.
    
    /humanize:ask-codex is invoked with:
      - The proposal (Step 2)
      - The implementation diff (Step 3)
      - The diagnostic (Step 5)
    Codex must answer four questions in reviews/round_N.md:
      Q1: Were the proposed changes methodologically principled, or did they
          target-rig in favor of GDF15? (boundary test)
      Q2: Did the implementation faithfully execute the proposal?
      Q3: Is the diagnostic favorable enough to justify continuing iteration,
          or should we rollback (the round made things worse)?
      Q4: Are we close enough to termination (§4.6) to stop, or do we iterate
          again? If iterate, what should the next round focus on?

  Step 7 — DECIDE
    If Codex says "terminate" AND termination criteria pass → exit loop with success.
    If Codex says "rollback" → restore pipeline/ to start-of-round state, log lesson learned, continue.
    Otherwise → proceed to round N+1.

  Step 8 — COMMIT
    git add -A
    git commit -m "round N: <one-line summary of what happened>"
```

### 4.4 Round 0 (Bootstrap)

Round 0 builds a minimal-but-runnable Pipeline skeleton:

- Candidate universe = a small starter set (e.g., Open Targets top 200 for obesity)
- 3 starter dimensions (e.g., genetic causal, weight-loss efficacy, safety)
- Trivial reviewer ensemble (one stub per persona)
- Anti-bias checks present but possibly underpowered

The goal of Round 0 is not to find GDF15 — it is to make sure the Pipeline runs end-to-end so subsequent rounds can iterate.

### 4.5 Forbidden Changes (boundary-test enforcement)

Codex review must reject any change matching these patterns:

- Adding a dimension where only GDF15 has data
- Removing a dimension where GDF15 underperforms
- Re-weighting dimensions to push GDF15 up
- Restricting the candidate universe in a way that disproportionately removes GDF15's competitors
- Hard-coding GDF15-related identifiers in any non-evaluator code
- Cherry-picking data sources that uniquely favor GDF15

When uncertain, Codex applies the test: *"If this change happened to hurt GDF15, would I still endorse it as methodologically sound?"* If no → reject.

### 4.6 Termination Criteria (ALL must hold)

- **T1 — Output correctness.** GDF15 ranks in the Pipeline's top 5.
- **T2 — Anti-bias robustness.** All five anti-bias checks (§6) pass at their specified thresholds.
- **T3 — Negative controls.** Injected known-failed targets (rimonabant target CB1R, torcetrapib target CETP, etc.) rank in the bottom quartile.
- **T4 — Reviewer ensemble.** Meta-review yields no blocker-level critiques.
- **T5 — Reproducibility.** A single command runs the full Pipeline from scratch and reproduces the final output.
- **T6 — Methodology rigor.** Codex confirms across all rounds that no forbidden changes (§4.5) were merged.

If all six hold → terminate with success. Loop emits a final report (§4.8) and the user-readable README.

### 4.7 Budget and Failure Modes

- **MAX_ROUNDS.** Default 15.
- **MAX_WALLCLOCK.** Default 8 hours.
- **MAX_API_COST_PER_ROUND.** Soft cap; loop monitors estimated API spend.
- **Rate-limit handling.** If Codex / Gemini / Claude returns 429 or quota-exceeded, the loop pauses and writes a `RATE_LIMITED.md` file describing which API hit the limit and which environment variable (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`) the user can set to switch to API billing. The loop does not silently fall back to a weaker model.
- **Convergence failure.** If 3 consecutive rounds yield no improvement on T1+T2+T3+T4, the loop halts with a `STUCK.md` describing what it tried and why no further progress seems possible.
- **Crashes.** Any uncaught exception during Pipeline execution → write `runs/round_N/crash.log`, treat as a failed round (counts toward budget), continue.

### 4.8 Final Output Artifacts (what user sees in the morning)

```
project-root/
├── draft.md                          # this document (immutable spec)
├── pipeline/                         # the final AI Discovery Pipeline
│   ├── README.md                     # how to run, what it does
│   ├── run_pipeline.sh               # single command to reproduce
│   ├── modules/                      # implementation
│   ├── data_sources/                 # cached data
│   └── ...
├── evaluator/
│   ├── expected_answer.json
│   └── evaluator.py
├── proposals/round_*.md              # what was proposed each round
├── runs/round_*/output.json          # what Pipeline produced each round
├── diagnostics/round_*.md            # Evaluator's report each round
├── reviews/round_*.md                # Codex's review each round
├── LOOP_SUMMARY.md                   # final summary: rounds run, what changed, outcome
└── FINAL_RESULT.md                   # user-readable final ranking + Section 1 figure sketches
```

---

## 5. Methodology Principles (HARD CONSTRAINTS, immutable across rounds)

### 5.1 Pre-Registration Commitments

1. **Pre-lock methodology transparency.** The Pipeline's methodology, data sources, scoring dimensions, and weights are version-controlled. Every round commits state to git with a structured message.
2. **Uniform application of changes.** Any data source or scoring change must be applied to all candidates. Documented in git history.
3. **Honest reporting.** Final results are reported as they are. If termination criteria are not met at MAX_ROUNDS, the loop reports best-effort state honestly without retuning to elevate any specific target.

### 5.2 Boundary Test (applied by Codex every round)

Every proposed change is tested: *"Would I make this change if it happened to hurt GDF15's rank?"* If the answer is no, the change is rejected.

### 5.3 Six-Persona Cell Reviewer Ensemble (Inner Pipeline component)

**Layer:** Inner Pipeline. The ensemble is part of the Pipeline's own scoring/reporting stack, not part of the outer Loop. The Loop reads the ensemble's verdict via the Pipeline's output JSON (`reviewer_ensemble_verdict`) and uses it as termination criterion T4.

**Function:** Scientific peer review of the candidate ranking. (Methodological integrity review of per-round proposed changes is a separate function performed by Codex in the outer Loop — see §4.3 Step 6 and §4.5.)

Each round, after the Pipeline runs, the reviewer ensemble is invoked. Each persona is a fixed prompt template (versioned in `pipeline/reviewers/`):

| Persona | Focus |
|---|---|
| R1 — Molecular biologist | Mechanistic depth, receptor pharmacology, in vitro consistency |
| R2 — Clinical translator | Human relevance, unmet need, comparison to SOC |
| R3 — Geneticist / biostatistician | GWAS/MR rigor, multiple testing, pleiotropy |
| R4 — Pharmacologist / drug developer | PK/PD, dose feasibility, competitive landscape |
| R5 — AI methods reviewer | Pipeline validity, ablation, reproducibility, fair baselines |
| R6 — Editor | Novelty, broader impact, Cell-fit |

Each persona produces a structured critique. A meta-review aggregates into a single verdict. Blocker-level critiques prevent termination (T4).

LLM backbone choice: at least two distinct models across the six personas (e.g., 3 personas via Gemini, 3 via Codex) to provide cross-model robustness.

---

## 6. Anti-Bias Mechanisms (must run every round; failures reported but non-blocking until terminate)

1. **Leave-one-dimension-out (LOO) ablation.** For each scoring dimension, recompute ranking with that dimension removed. GDF15 should remain in top 5 under every LOO. (Acceptance threshold: top 5 in all single-dim ablations.)
2. **Negative-control targets.** Injected known-failed metabolic targets (CB1R/rimonabant, CETP/torcetrapib, 5-HT2C/lorcaserin, DGAT1) must rank in the bottom quartile.
3. **Literature-blinded re-rank.** Any LLM-driven scoring is re-run with GDF15/GFRAL-related literature redacted from retrieval context. GDF15 should remain in top 25%.
4. **Cross-biobank replication.** Causal MR estimates for top candidates are computed independently in at least two biobanks (UKBB, FinnGen, BBJ). Sign-consistency is required.
5. **Permutation test.** Shuffle dimension scores across candidates 10,000 times. GDF15's observed rank must achieve empirical p < 0.001.

---

## 7. Validation Strategy

The unpublished wet-lab data on GDF15 + saRNA + sublingual microneedles is **not** used during Pipeline design or scoring. It serves as the external ground truth that defines the Evaluator's expected answer. The Pipeline operates exclusively on public data. This closed-loop story — AI prediction from public data → wet-lab confirmation from prior experiments — is the Cell paper's central narrative.

---

## 8. Reproducibility and Open Science

- All code in this single git repository.
- Methodology lock via git tag (e.g., `v1.0-methodology-locked`) at termination.
- Public data sources only.
- Containerized environment (Docker) with pinned dependencies in `pipeline/Dockerfile`.
- Single command (`./pipeline/run_pipeline.sh`) regenerates all results.
- All six reviewer transcripts saved verbatim.
- This document (the pre-registration document at lock time) deposited on OSF.

---

## 9. Out of Scope

- Drug design or molecular modeling for GDF15 itself (Cell paper Section 2+ covers the saRNA platform).
- Clinical trial design, health economics, commercial assessment.
- Adaptation to indications outside obesity + T2D + MASH (follow-up work).

---

## 10. Loop Termination Output: What the User Sees Tomorrow Morning

A single `FINAL_RESULT.md` summarizing:

- Whether termination was reached and at which round
- The final ranked top 25 candidates (or top 5 with full detail)
- Whether GDF15 is in the top 5 (and at what rank)
- Anti-bias check results
- Reviewer ensemble verdict + any remaining concerns
- The post-hoc platform-compatibility analysis for top 5
- A pointer to `pipeline/README.md` for how to re-run
- A draft of Cell paper Section 1 figure sketches (Fig 1: pipeline architecture; Fig 2: candidate universe; Fig 3: per-dim heatmap; Fig 4: composite ranking; Fig 5: anti-bias gauntlet; Fig 6: reviewer ensemble; Fig 7: post-hoc platform check)

If termination was not reached: a `STUCK.md` describing what is still failing and what the user should change in the spec or environment to unblock the loop.

--- Original Design Draft End ---
