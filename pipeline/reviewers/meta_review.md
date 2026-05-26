# Meta-Review Aggregator

## Purpose
Aggregate the six per-persona reviews (R1-R6) into a single verdict with:
- Cross-reviewer agreement matrix (which concerns appeared in multiple reviewers)
- Consolidated blocker list (deduplicated across personas)
- Overall recommendation (proceed / fix-blockers-then-proceed / major-revision-required)
- An explicit `blockers_remaining` array that downstream code uses for termination decisions

## Aggregation Rules
1. A concern is a "consensus blocker" if 2+ personas flag it as blocker-severity.
2. A concern flagged by only one persona as blocker remains in `blockers_remaining` but is labeled "single-reviewer".
3. Pipeline-level methodology critiques (from R3 and R5) are surfaced separately from per-candidate critiques.
4. The meta-review must include a `verdict` field with one of: `pass`, `pass_with_minor_revisions`, `major_revision_required`, `reject_with_resubmission`.

## Output Schema
```json
{
  "meta_review": {
    "verdict": "pass | pass_with_minor_revisions | major_revision_required | reject_with_resubmission",
    "consensus_blockers": [...],
    "single_reviewer_blockers": [...],
    "pipeline_methodology_concerns": [...],
    "cross_reviewer_agreement_summary": "..."
  },
  "blockers_remaining": [...]
}
```
