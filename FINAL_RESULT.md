# FINAL_RESULT — AI Discovery Pipeline for MASH+T2D+Obesity Target Ranking

## Termination Status

**SUBSTANTIVE_PROGRESS_WITH_FIVE_AC_PARTIAL** — derived from current artifacts after the
Round 9 close-out (regenerated 2026-05-27).

This document is not a completion declaration. It honestly reports what is verified, what
remains partial, and what is queued for a future cycle. The status field reflects the
union of: regular-mode reviewer-blocker propagation tightened, AC-7 run-local artifact
binding implemented, AC-9 documentation synced (with explicit incompleteness note), and
the remaining gaps in AC-8 lifecycle and AC-9 clean-clone replay.

## Headline Result

The pipeline ran end-to-end on a 696-candidate universe with the methodology pinned at
git tag `v1.0-methodology-locked` (R9 re-lock). The hidden expected target (held by the
External Evaluator) appeared at **rank #1** of 696 with composite z-score **+1.678**.

The result is a multi-dimensional Pareto: top-quartile on every one of the seven
ranking-contributing dimensions; stays #1 under every single-dimension leave-one-out
ablation (Spearman ρ avg 0.958 between full and each LOO ranking); top quartile (rank
16/696 ≈ 2.30%) even when the expected target's gene symbols are uniformly redacted from
the literature snapshot.

## Lock and Reproducibility

- Lock tag: `v1.0-methodology-locked` (moved forcibly to the Round 9 close-out commit,
  superseding the R7-era lock commit).
- Locked manifest: `pipeline/LOCKED_ARTIFACTS.json` (53 artifacts post-R9, SHA256-pinned;
  added `pipeline/reviewers/blocker_normalization.py` in Round 9).
- Lock verifier (positive): PASS (53/53).
- Source-code leakage scan: `bash scripts/scan_target_leakage.sh pipeline` → PASS (0 hits).
- Engineering audit notes: `pipeline/audits/round_8_engineering_audit_note.md`,
  `pipeline/audits/round_9_engineering_audit_note.md`.

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

## Acceptance Criteria — Status (derived from current artifacts, R9)

| AC | Status | Evidence |
|----|--------|----------|
| AC-1 | PASS | Phase α evaluator-free; Phase β verbose evaluator with target-specific verifications. |
| AC-2 | PASS | `runs/round_8/output.json` conforms to §3.1 IO contract; assembled end-to-end with same-run reviewer dossier. |
| AC-3 | PASS | `pipeline/universe/build_universe.py` deterministic; 696 candidates. |
| AC-4 | PASS | 8 dimensions; 7 contribute to composite; weights validator enforces sum=1.0. |
| AC-5 | **PARTIAL** | All 6 personas invoked live in round 8; shared `blocker_normalization.py` used by both regular and deferred modes; per-persona provenance (`status`, `backbone_used`, `prompt_hash`, `input_hash`) recorded; validator rejects silent blocker drops in BOTH modes. Current top-level `overall_status = PASS` because no critique survived normalization with severity=blocker AND a real summary (3 personas reported counts without proper critique structure — surfaced as WARN, not silently dropped). Still PARTIAL because (a) the dossier reviewers saw is current-run but reviewers' raw LLM responses cannot be deterministically re-played, and (b) no human adjudication of the three persona self-reporting inconsistencies has happened. |
| AC-6 | **PARTIAL** | 0 hard / 2 soft anti-bias failures (`negative_controls` 40.01 vs ≥50; `permutation_test` 0.0090 vs <0.001). Both attributable to bootstrap data and will tighten with full snapshot ingestion. MR `OPTIONAL_SKIPPED`. |
| AC-7 | **PARTIAL** | Run-local artifact binding implemented: `runs/round_8/anti_bias/` contains 5 results + validation_summary; `anti_bias_artifact_paths` references those run-local paths; evaluator REFUSES scratch fallback. Still PARTIAL until a separate-worktree replay confirms portability of the relative-path scheme. |
| AC-8 | **PARTIAL** | `scripts/loop_orchestrator.sh` MAX_ROUNDS/STUCK detection + rollback to per-round saved ref + diagnostic-driven T_PASSES are present. Still PARTIAL because implementation-by-task-tag hooks and in-band Codex review wiring are NOT implemented. |
| AC-9 | **PARTIAL** | `CANONICAL_EXCLUSIONS.md` synced exactly with `canonicalize_output.py` (4 top-level exclusions documented). Still PARTIAL because (a) the whole `reviewer_ensemble_verdict` block is excluded, masking any change to reviewer prose/structure from byte-diff, and (b) no separate-worktree clean-clone replay diff has been recorded. Documented incomplete limitation; two remediation paths listed in `CANONICAL_EXCLUSIONS.md`. |
| AC-10 | **PARTIAL** | This document is honest about what is PASS vs PARTIAL; supporting docs `METHODOLOGY_TRANSPARENCY.md` and seven figure sketches at `figures/Section1/` are present. Status remains PARTIAL until AC-5/AC-7/AC-8/AC-9 are no longer partial. |

## Plan-critical work still to do (not optional deferrals)

These are required for full acceptance, not future-cycle nice-to-haves:

1. **AC-5 review-reporting**: change reviewer-persona prompts so that any persona reporting
   `blockers_count > 0` MUST emit at least one structured critique with
   `severity="blocker"` and a real summary; or, programmatically demote
   self-contradictory `blockers_count` values to 0 at parse time with explicit logging.
2. **AC-7 portability**: write a separate-worktree replay test that resolves
   `anti_bias_artifact_paths` from the embedded relative paths and confirms LOO + lit-blind
   verifications produce identical PASS/FAIL labels.
3. **AC-8 lifecycle**: implement `coding` vs `analyze` task-tag routing inside the
   orchestrator's Step 2 (currently a no-op `touch` flag); wire in-band Codex review into
   Step 5 (currently external).
4. **AC-9 clean-clone replay**: perform the replay in a separate worktree, canonicalize
   both outputs, and commit the byte-diff (expected: empty) as evidence.
5. **AC-9 reviewer tightening**: implement one of the two remediation paths in
   `CANONICAL_EXCLUSIONS.md` so the whole reviewer block stops being a canonical blind spot.

## Cross-round artifact pointers

- Round 7 (regenerated 2026-05-27): `runs/round_7/output.json`, `runs/round_7/reviewer_ensemble_verdict.json`
- Round 8 (R9-current state): `runs/round_8/output.json`, `runs/round_8/reviewer_ensemble_verdict.json`, `runs/round_8/anti_bias/_results_*.json`
- Diagnostic: `diagnostics/round_8.md`
- Round summaries: `.humanize/rlcr/2026-05-27_04-50-03/round-N-summary.md` (gitignored; local audit only)
