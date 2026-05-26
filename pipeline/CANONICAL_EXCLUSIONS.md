# Canonicalization Exclusions

For AC-9 reproducibility comparison via `scripts/canonicalize_output.py`, the following
fields are excluded from byte-identity comparison because they depend on runtime state
(git history at time of run, system timestamps, etc.) but do not reflect Pipeline correctness:

## Top-level exclusions
- `pre_registration_hash` — depends on the git tag/HEAD SHA at the moment the Pipeline ran. Independent runs at different commits will differ here but produce identical scientific content.

## reviewer_ensemble_verdict exclusions
- `round` — the round-number metadata is bookkeeping
- `mode` — `MOCK_STUB_FOR_ROUND_0` vs `REGULAR` is a deployment detail

## NOT excluded (must match for reproducibility)
- All ranked_targets entries (rank, score, per_dim_scores, predictions)
- All anti_bias_validation fields (LOO, NC, lit-blinded, MR status, permutation p)
- weights_used and dimensions_excluded_from_composite

Any future addition to the exclusion list must be justified by a Round summary entry
and approved by Codex review in the post-lock audit.
