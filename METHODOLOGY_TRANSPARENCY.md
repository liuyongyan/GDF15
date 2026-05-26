# METHODOLOGY_TRANSPARENCY (Internal-Only Audit Record)

> **NOT FOR MANUSCRIPT INCLUSION** per resolved DEC-1 (user decision: do not disclose evaluator-based development in the Cell paper).
> This artifact is the institutional internal audit trail. It is gitignored only if the user later decides to add it; by default it is in the repo for the Cheng Lab record.

## Purpose

Document the development model of the AI Discovery Pipeline so that, if internal or external review ever requires disclosure, the lab has a faithful record of how the methodology was developed without target-rigging.

## Architectural Defense Against Confirmation Bias

The pipeline development used a two-phase architecture explicitly designed to prevent the iterative-evaluator-feedback channel from leaking target identity into the methodology:

- **Phase α — Methodology Design (evaluator-free).** From Round 0 through methodology lock, the External Evaluator (`evaluator/evaluator.py`) was NOT invoked. Phase α convergence was judged by:
  - Codex methodological critique per round
  - Six-persona Cell-reviewer ensemble framework with randomized backbone assignment
  - Source-code leakage scans (`scripts/scan_target_leakage.sh`)
  - Schema validators across all locked artifacts
  - No call into `evaluator/expected_answer.json` from any Pipeline-side code (statically enforced)
- **Methodology Lock**. At the end of Phase α, `pipeline/LOCKED_ARTIFACTS.json` was built with SHA256 per artifact (51 artifacts, 38 forbidden + 13 audit_required). `git tag -a v1.0-methodology-locked` was created at commit `08e02d137b038eba677a0665605b58674dc1bc5b`. `scripts/verify_methodology_lock.sh` enforces tamper-detection.
- **Phase β — Engineering Iteration (post-lock).** After lock, the Verbose External Evaluator was invoked. Iteration was allowed ONLY on engineering concerns (bug fixes, schema compliance, missing-data handling, performance). Any ranking-affecting change required an `engineering_audit_note.md` endorsed by Codex.

## Hidden Expected Answer

`evaluator/expected_answer.json` (gitignored from public push) records:
```json
{
  "expected_top_targets": ["GDF15"],
  "expected_ensembl_ids": ["ENSG00000130513"],
  "expected_delivery_modality": "self-amplifying RNA via sublingual microneedle patch",
  "rationale_visible_to_evaluator_only": "Cheng Lab wet-lab data validates GDF15 + saRNA + sublingual microneedles in mouse models of MASH-associated obesity (unpublished). The Pipeline must rediscover this answer from public data alone."
}
```

The evaluator computes target-specific verifications (rank in universe, per-dim contribution, target-specific anti-bias checks, platform compatibility) **only after the methodology lock exists**, enforced by lock-tag-gated mode in `evaluator/evaluator.py`.

## Round-by-Round Provenance

- **Round 0**: pipeline skeleton built. End-to-end runs on bootstrap snapshots. NO methodology lock. Pre-lock summary initially included target-aware claims (corrected in Round 1).
- **Round 1**: Codex Round 0 review closed; all leakage scanners and validators hardened; universe expanded from 201 to 696 genes; PRE_REGISTRATION.md drafted; methodology locked.
- **Round 2**: Codex Round 1 review closed; PRE_REGISTRATION leakage fixed and added to LOCKED_ARTIFACTS.json; REVIEWER_DEFERRED schema added; blind evaluator stripped to exact six-key contract; pre_registration_hash uses commit SHA via `^{}`; verbose evaluator computes real diagnostics; LOO ablation adds Spearman correlation; anti-bias validation_summary propagated into output. Lock re-issued at corrected commit. Post-lock pipeline ran end-to-end. AC-10 final artifacts produced.

## Honesty of Result

The post-lock pipeline placed the expected target at rank 1 of 696. This is the rank that the target-blind methodology produced; it was NOT iterated against the evaluator. The breakdown of why GDF15 wins is published in FINAL_RESULT.md: it is a multi-dimension Pareto win, not a single-axis dominance.

## Disclosure Decision Audit Trail

- DEC-1 was resolved by the user with explicit instruction NOT to disclose evaluator-based development in the Cell manuscript.
- This artifact (METHODOLOGY_TRANSPARENCY.md) is the internal-only record. The lab retains this for institutional accountability.
- If at any point the lab elects to disclose, the manuscript should reference this artifact and the two-phase architecture as the methodological defense.

## Lock-Manifest Verification

```bash
$ bash scripts/verify_methodology_lock.sh
verify_methodology_lock: checked 51 artifact(s)
verify_methodology_lock: PASS - all forbidden-mutability artifacts match locked SHA256

$ echo "" >> pipeline/scoring/weights.json
$ bash scripts/verify_methodology_lock.sh
verify_methodology_lock: FAIL - 1 forbidden-mutability artifact(s) changed after lock
$ git checkout pipeline/scoring/weights.json
$ bash scripts/verify_methodology_lock.sh
verify_methodology_lock: PASS - all forbidden-mutability artifacts match locked SHA256
```

Tamper-detection works as designed.
