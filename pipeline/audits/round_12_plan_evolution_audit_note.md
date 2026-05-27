# Engineering Audit Note — Round 12 (Plan Evolution) — 2026-05-27

## Purpose
Round 12 is a **plan-evolution** round, not a code-fix round. The user reviewed the
R11 close-out artifacts manually and added two new requirements to the project:

1. Each pipeline round must emit a self-contained, human-readable walkthrough at
   `runs/round_N/round_N_walkthrough.md` describing what each pipeline step did,
   why, and what it produced.
2. Cell paper Section 1 figures must be publication-grade plots produced by an
   R script (`figures/Section1/generate_figures.R`), not ASCII/Markdown sketches.

These requirements are encoded as two new acceptance criteria — **AC-11** and **AC-12**
— added to `plan.md` in this round. Three new tasks (task29, task30, task31) are added
to the task breakdown.

## Why this is an engineering re-lock (not a methodology revision)

The new ACs are **reporting-additivity** changes. Both AC-11 (walkthrough generator)
and AC-12 (R figures) describe **outputs of the pipeline**, not the **ranking
algorithm**. They satisfy all four conditions for the engineering audit-required path:

1. **No change to scoring**: weights.json, dimensions.json, per-dim scorers are untouched.
   The ranked top-N for any given input remains bit-identical.
2. **No change to anti-bias mechanisms**: LOO, NC, lit-blinded, MR, permutation are untouched.
3. **No change to reviewer ensemble**: the six personas, dossier construction, validator,
   blocker normalization are untouched. The walkthrough READS the reviewer verdict; it
   does not modify it.
4. **No change to lock policy**: `LOCKED_ARTIFACTS.json` SHA256 enforcement, source
   leakage scanning, and reviewer-prose forbidden-name redaction remain unchanged.

Per the established R8–R11 protocol, plan.md is `mutability=forbidden` and changing it
post-lock requires this audit note, a manifest hash refresh, and a force-move of
`v1.0-methodology-locked` to the close-out commit.

## Forbidden-mutability artifacts changed (1)

### 1. `plan.md`
- **AC ref**: AC-1 (lock policy: forbidden artifact change requires audit note),
  AC-10 (final report scope), AC-11 (new), AC-12 (new)
- **Change**:
  - Added AC-11 (round walkthrough generator + 5 positive tests + 2 negative tests)
    and AC-12 (R publication-grade figures + 5 positive tests + 2 negative tests) to
    the `## Acceptance Criteria` section, immediately after AC-10.
  - Added task29 (walkthrough generator, depends on task12), task30 (R figure script,
    depends on task25), and task31 (post-AC-11/AC-12 re-lock + tag move, depends on
    task29 and task30) to the `## Task Breakdown` table.
- **Why**: User-supplied requirement additions; engineering reporting-additivity (no
  scoring/ranking change).
- **Target-blind**: yes (both new ACs are blind to the expected target; AC-11 may
  reference candidate gene symbols only when reading post-evaluator artifacts, which
  is the same target-policy as `FINAL_RESULT.md` already follows).

## Files deleted (7)

### 2-8. `figures/Section1/Fig{1..7}*.md`
- **AC ref**: AC-10 → AC-12 supersession
- **Change**: legacy ASCII/Markdown figure sketches removed. AC-12 explicitly
  supersedes the AC-10 sketch requirement; the R script that AC-12 introduces will
  produce publication-grade PNG/PDF replacements.
- **Why**: user confirmed deletion is OK; preserving sketches as alongside R outputs
  would create dual-source-of-truth ambiguity about which is the canonical figure.
- These files are NOT in LOCKED_ARTIFACTS.json (no SHA pinned), so removal does not
  require a manifest entry change. The deletion is recorded here for audit traceability.

## Re-lock action
- `pipeline/LOCKED_ARTIFACTS.json`: refresh the `plan.md` sha256 hash.
- `v1.0-methodology-locked` tag: force-move to the Round 12 close-out commit.
- No pipeline re-run is required for this round: AC-11 and AC-12 are NOT yet
  implemented in this round; they are added to plan.md as new ACs and will be picked
  up by the next RLCR loop invocation. The Round 12 commit is a spec-only change.

## What happens next
The user will re-launch `/humanize:start-rlcr-loop plan.md`. The RLCR loop will see
AC-11 and AC-12 as new unmet ACs and iterate to implement task29 + task30 + task31.
Codex review will adjudicate the implementations under the same evidence-honesty
discipline R8–R11 enforced.
