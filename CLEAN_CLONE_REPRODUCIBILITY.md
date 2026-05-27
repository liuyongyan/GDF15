# Clean-Clone Reproducibility Validation Report (AC-9)

## Procedure

```bash
git clone . /tmp/gdf15_clean_clone
cd /tmp/gdf15_clean_clone
git checkout v1.0-methodology-locked
mkdir -p runs
cp -r <main-repo>/runs/reviewer_cache runs/
mkdir -p runs/clean
bash pipeline/run_pipeline.sh sample_input.json runs/clean/output.json 99
# Canonicalize and diff against main repo reference output
python3 scripts/canonicalize_output.py /tmp/gdf15_clean_clone/runs/clean/output.json - > /tmp/clean_canon.json
python3 scripts/canonicalize_output.py runs/round_3/output.json - > /tmp/ref_canon.json
diff /tmp/clean_canon.json /tmp/ref_canon.json
```

## Result

**Deterministic fields:** all MATCH byte-for-byte.

| Field | Status |
|-------|--------|
| `ranked_targets` (696 candidates with composite_score, per_dimension_scores, predictions) | **MATCH** |
| `ranked_targets_full_count` | **MATCH** |
| `anti_bias_validation` (LOO, NC, lit-blinded, MR, permutation) | **MATCH** |
| `weights_used` | **MATCH** |
| `dimensions_excluded_from_composite` | **MATCH** |
| `reproducibility` | **MATCH** |
| `schema_version` | **MATCH** |

**Non-deterministic fields:**

| Field | Status | Reason |
|-------|--------|--------|
| `round` | DIFFER (99 vs 3) | Round number is an explicit command-line argument; differing values are correct. |
| `reviewer_ensemble_verdict` | DIFFER (which personas had cache hits) | The reviewer ensemble is allowed to be non-deterministic per AC-5 (real LLM responses are inherently variable). For byte-comparable reproducibility, the verdict block could be additionally excluded from canonicalization, but the cache mechanism means cache-hit personas are reproducible. |

## Sizes

- Clean-clone canonicalized output: 92,986 bytes
- Reference canonicalized output: 89,534 bytes
- Diff lines: 43 (entirely within `reviewer_ensemble_verdict` block + the round number)

## Interpretation

The Pipeline's **scientific output** (the candidate universe, ranking, scoring, and anti-bias gauntlet results) is fully reproducible from a clean clone of the methodology-locked commit. The deterministic portion of the output JSON is byte-identical across independent runs.

The reviewer ensemble verdict portion is inherently non-deterministic when real LLM invocations are involved (LLM responses vary across calls; cache hits depend on whether previous runs successfully captured each persona's response). This non-determinism is documented and expected under the AC-5 contract.

For full byte-identical reproducibility of the entire output JSON, the canonicalizer would also need to exclude or hash the reviewer_ensemble_verdict block. This is a documented limitation rather than a methodology defect.

## AC-9 Status: **PASS (deterministic) + DOCUMENTED-PARTIAL (reviewer block)**

The single-command rerun produces the locked pipeline output. The scientific portion is reproducible byte-for-byte. The reviewer ensemble portion's non-determinism is acknowledged in the methodology and is consistent with AC-5's allowance for live LLM variability.
