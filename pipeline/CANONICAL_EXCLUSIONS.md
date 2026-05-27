# Canonicalization Exclusions

For AC-9 reproducibility comparison via `scripts/canonicalize_output.py`, the following
top-level fields are excluded from byte-identity comparison. This file must stay **exactly
in sync** with `EXCLUDE_TOPLEVEL` in `scripts/canonicalize_output.py`.

## Top-level exclusions (4)
- `pre_registration_hash` — the commit SHA bearing the lock tag at run time. Independent
  runs at different commits produce identical scientific content with different hashes.
- `round` — the round number is an explicit CLI argument; different values are correct,
  not a methodology difference.
- `reviewer_ensemble_verdict` — the entire reviewer-ensemble block is excluded because
  real LLM responses are non-deterministic across runs (cache state, provider failover,
  inherent LLM stochasticity). The verdict is preserved verbatim at
  `runs/round_N/reviewer_ensemble_verdict.json` for audit but does not participate in
  byte-comparison. **See AC-9 Limitation below.**
- `anti_bias_artifact_paths` — these are run-local paths into `runs/round_N/anti_bias/`
  (relative to repo root when possible, otherwise absolute). Paths vary per checkout
  location but reference identical artifact content (which IS canonically compared via
  `anti_bias_validation`).

## NOT excluded (must match for reproducibility)
- All `ranked_targets` entries (rank, score, per_dim_scores, predictions)
- All `anti_bias_validation` fields (LOO summary, NC summary, lit-blinded summary,
  MR status, permutation p-value, `validation_summary` mechanism statuses)
- `ranked_targets_full_count`
- `schema_version`
- `weights_used` and `dimensions_excluded_from_composite`
- `reproducibility` (the command string)

## AC-9 Limitation (acknowledged, INCOMPLETE)
The current implementation excludes the **entire** `reviewer_ensemble_verdict` block from
canonical comparison. This means a malicious or accidental change to reviewer prose,
per-persona structure, or aggregated blockers would NOT surface in an AC-9 byte-diff. This
is a documented incomplete limitation. Two future-cycle remediation paths are open:

1. **Tighten the exclusion**: cache per-persona parsed verdicts deterministically by
   `(prompt_hash, input_hash)` and include the parsed sub-tree in canonical comparison;
   keep only `raw_text` / `raw_text_sha1` / status fields excluded.
2. **Replace with content hash**: replace the verdict block in the canonical document with
   `reviewer_ensemble_verdict_sha256` of the canonicalized parsed content, surfacing any
   change as a single hash diff.

Additionally, separate-worktree / clean-clone replay evidence has NOT yet been recorded.
Until both the exclusion is tightened (or replaced with a content hash) AND a clean-clone
replay diff is captured, **AC-9 must be reported as PARTIAL**, not PASS.

Any future addition to or removal from the exclusion list MUST update this file in the
same commit that changes `scripts/canonicalize_output.py`, and must be justified in the
round summary and approved by Codex review.
