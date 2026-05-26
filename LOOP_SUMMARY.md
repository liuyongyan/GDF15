# Loop Summary

> Honest, target-agnostic summary of the two-phase autonomous loop's progress through Round 1.
> Maintained across rounds; Phase β progress will be appended after each Phase β round.

## Architecture

- **Phase α** (Rounds 0-1): evaluator-free methodology design + lock.
- **Phase β** (Rounds 2+): post-lock engineering iteration with verbose evaluator.
- Phases separated by `git tag v1.0-methodology-locked` and `pipeline/LOCKED_ARTIFACTS.json` (SHA256-pinned).

## Round 0 (skeleton)

- Provisioned the file tree: `pipeline/`, `evaluator/`, `scripts/`, plus 57 source files.
- All scripts executed end-to-end on bootstrap data snapshots.
- Pre-lock pipeline output existed but was treated as engineering verification, NOT AC-2-compliant.
- Codex Round 0 review found several validator gaps, a target-name leak in `anti_bias/thresholds.json`, a scanner that excluded JSON configs, a permissive preflight, mock-only reviewer ensemble, undersized universe (201), and a target-aware claim in the original round-0-summary.

## Round 1 (lock)

Fixes applied to address every Codex Round 0 mainline gap:

| Gap | Round 1 fix |
|-----|-------------|
| `anti_bias/thresholds.json` notes leaked target identifier | notes rewritten to target-agnostic language |
| `scan_target_leakage.sh` excluded all `*.json` | scanner now includes JSON configs, excluding only derived data outputs |
| `run_pipeline.sh` accepted missing input | `validate_input.py` enforces required fields and `run_pipeline.sh` exits non-zero on validation failure |
| Anti-bias validator silently passed on threshold failures | `validate_suite_output.py` now reads `thresholds.json`, computes per-mechanism PASS/FAIL/MISSING, emits `_validation_summary.json`, and fails on hard-severity violations |
| Evaluator blind mode returned Markdown | `--mode blind` now returns AC-1.1 categorical JSON only (T1..T6 booleans, no target identifiers) |
| `preflight.sh` permissive on dirty git | dirty git now fails preflight; snapshot SHA256 manifest verified against `pipeline/data_sources/SNAPSHOT_HASHES.txt` |
| Universe 201 below immutable 500-2000 | augmented snapshots via `pipeline/data_sources/augment_snapshots.py`; universe now 696 genes, diversity check still PASSES |
| Reviewer validator accepted MOCK_STUB silently | validator now rejects MOCK_STUB if `v1.0-methodology-locked` tag exists |
| Round 0 summary disclosed target rank pre-lock | round-0-summary rewritten to be target-agnostic; methodology lesson recorded |
| Methodology lock missing | `pipeline/LOCKED_ARTIFACTS.json` (50 artifacts, 37 forbidden + 13 audit_required, SHA256 per artifact); `pipeline/PRE_REGISTRATION.md`; `git tag v1.0-methodology-locked` (SHA `ec350d7079acbcb3f466e4fbb714f2ebb4707ff0`) |
| Lock verifier untested | positive test PASS; negative test (touch `pipeline/scoring/weights.json`) returns exit 1 |

## Methodology Lock — Pre-Registration Summary

- **Tag**: `v1.0-methodology-locked`
- **Commit SHA**: `8f7741ebad25b8b023eade4e1a3a01084f921b17`
- **Manifest**: `pipeline/LOCKED_ARTIFACTS.json` (50 artifacts)
- **Pre-registration doc**: `pipeline/PRE_REGISTRATION.md`
- **Universe at lock**: 696 protein-coding gene entries (within immutable 500-2000 range)
- **Scoring**: 8 dimensions in `dimensions.json`; 7 ranking-contributing + 1 excluded (platform_deliverability); weights sum 1.0, max 0.143
- **Anti-bias suite**: 5 mechanisms; target-agnostic Pipeline-side thresholds; target-specific verifications in `evaluator/expected_thresholds.json`
- **Reviewer ensemble**: 6 personas; randomized backbone (codex/gemini) by deterministic round seed; MOCK_STUB usable only pre-lock
- **Evaluator**: `evaluator/evaluator.py` mode-gated on lock tag

## Phase α Convergence Statement

After Round 1, Phase α is considered converged at the methodological-rigor level Codex flagged. Convergence judged target-blindly per AC-1.1:

- All five categories of source-code/config leakage scans PASS
- All five anti-bias mechanisms produce structured outputs with explicit threshold pass/fail
- Reviewer ensemble dry-run validates schema; real-LLM activation is a Phase β engineering task
- Methodology lock verified (positive + negative tests)

The pre-lock pipeline output was treated as engineering verification only. The first AC-2-compliant output (with `pre_registration_hash` = locked tag SHA) will be produced in Phase β.

## Round 2+ Outline

- **Round 2 (Phase β kick-off)**: invoke `evaluator/evaluator.py --mode verbose`; produce first locked pipeline output; observe target ranking; begin `FINAL_RESULT.md` draft; write `METHODOLOGY_TRANSPARENCY.md` (internal-only per DEC-1).
- **Round 3+**: real Codex/Gemini reviewer ensemble integration (subject to subscription budget; on rate limit, write `RATE_LIMITED.md` per user-prescribed protocol).
- **Round N (final)**: write 7 figure sketches; clean-clone reproducibility validation; final commit.

## Pre-Registration Hash Notice

The Pipeline output from this point forward will set `pre_registration_hash` to the locked tag SHA `ec350d7079acbcb3f466e4fbb714f2ebb4707ff0` instead of the `HEAD_pre_lock` placeholder used in Round 0.
