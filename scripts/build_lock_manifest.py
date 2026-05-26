#!/usr/bin/env python3
"""Build pipeline/LOCKED_ARTIFACTS.json — the methodology-lock SHA256 manifest.

Enumerates every artifact whose contents define the locked methodology:
  - pipeline/scoring/dimensions.json
  - pipeline/scoring/weights.json
  - pipeline/scoring/score_*.py
  - pipeline/scoring/scoring_lib.py
  - pipeline/scoring/validate_weights.py
  - pipeline/anti_bias/thresholds.json
  - pipeline/anti_bias/*.py
  - pipeline/anti_bias/run_suite.sh
  - pipeline/universe/build_universe.py
  - pipeline/reviewers/*.md
  - pipeline/reviewers/config.json
  - pipeline/reviewers/FORBIDDEN_TARGET_NAMES.txt
  - pipeline/reviewers/run_ensemble.sh   [mutability: audit_required — LLM backbone may upgrade]
  - pipeline/reviewers/validate_ensemble_output.py
  - pipeline/reviewers/scan_reviewer_outputs.py
  - pipeline/post_hoc/platform_compatibility.py
  - pipeline/assemble_output.py
  - pipeline/validate_input.py
  - pipeline/run_pipeline.sh
  - pipeline/data_sources/MANIFEST.md
  - pipeline/data_sources/SNAPSHOT_HASHES.txt   [hashes lock the snapshot bytes themselves]
  - evaluator/evaluator.py
  - scripts/scan_target_leakage.sh
  - scripts/verify_methodology_lock.sh
  - scripts/scan_api_calls.sh
  - scripts/preflight.sh
  - scripts/canonicalize_output.py
  - scripts/loop_orchestrator.sh
  - scripts/build_snapshot_manifest.sh
  - draft.md
  - plan.md

Each entry has: path, purpose, sha256, mutability ∈ {forbidden, audit_required}.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def build_artifact(path_str: str, purpose: str, mutability: str) -> dict:
    p = REPO_ROOT / path_str
    if not p.exists():
        return {
            "path": path_str,
            "purpose": purpose,
            "mutability": mutability,
            "sha256": None,
            "status": "MISSING_AT_LOCK_TIME",
        }
    return {
        "path": path_str,
        "purpose": purpose,
        "mutability": mutability,
        "sha256": sha256_of(p),
    }


def main() -> int:
    entries: list[dict] = []

    # methodology spec
    entries.append(build_artifact("draft.md", "Immutable spec the loop must satisfy", "forbidden"))
    entries.append(build_artifact("plan.md", "Implementation plan with locked AC", "forbidden"))
    entries.append(build_artifact("pipeline/PRE_REGISTRATION.md", "Pre-registration manifest pinned by the lock tag", "forbidden"))

    # Scoring layer
    entries.append(build_artifact("pipeline/scoring/dimensions.json", "Scoring dimension definitions", "forbidden"))
    entries.append(build_artifact("pipeline/scoring/weights.json", "Composite-ranking weights", "forbidden"))
    entries.append(build_artifact("pipeline/scoring/scoring_lib.py", "Shared scoring utilities", "audit_required"))
    entries.append(build_artifact("pipeline/scoring/validate_weights.py", "Weights schema validator", "audit_required"))
    for score_path in sorted((REPO_ROOT / "pipeline" / "scoring").glob("score_*.py")):
        rel = score_path.relative_to(REPO_ROOT).as_posix()
        entries.append(build_artifact(rel, "Per-dimension scorer", "forbidden"))

    # Universe builder
    entries.append(build_artifact("pipeline/universe/build_universe.py", "Deterministic universe builder", "forbidden"))

    # Anti-bias
    entries.append(build_artifact("pipeline/anti_bias/thresholds.json", "Target-agnostic anti-bias thresholds", "forbidden"))
    entries.append(build_artifact("pipeline/anti_bias/anti_bias_lib.py", "Anti-bias shared utilities", "audit_required"))
    for ab in ("loo_ablation.py", "negative_controls.py", "literature_blinded.py", "cross_biobank_mr.py", "permutation_test.py", "validate_suite_output.py", "run_suite.sh"):
        entries.append(build_artifact(f"pipeline/anti_bias/{ab}", "Anti-bias mechanism", "forbidden"))

    # Reviewer ensemble
    for r in ("R1_molecular_biologist.md", "R2_clinical_translator.md", "R3_geneticist_biostatistician.md", "R4_pharmacologist.md", "R5_ai_methods_reviewer.md", "R6_editor.md", "meta_review.md"):
        entries.append(build_artifact(f"pipeline/reviewers/{r}", "Reviewer persona prompt", "forbidden"))
    entries.append(build_artifact("pipeline/reviewers/FORBIDDEN_TARGET_NAMES.txt", "Target-name redaction list", "forbidden"))
    entries.append(build_artifact("pipeline/reviewers/config.json", "Reviewer ensemble configuration", "audit_required"))
    entries.append(build_artifact("pipeline/reviewers/run_ensemble.sh", "Ensemble invocation", "audit_required"))
    entries.append(build_artifact("pipeline/reviewers/validate_ensemble_output.py", "Reviewer output validator", "forbidden"))
    entries.append(build_artifact("pipeline/reviewers/scan_reviewer_outputs.py", "Reviewer leakage scanner", "forbidden"))

    # Pipeline orchestration
    entries.append(build_artifact("pipeline/run_pipeline.sh", "End-to-end pipeline orchestrator", "audit_required"))
    entries.append(build_artifact("pipeline/assemble_output.py", "Output schema assembler", "audit_required"))
    entries.append(build_artifact("pipeline/validate_input.py", "Input contract validator", "forbidden"))
    entries.append(build_artifact("pipeline/post_hoc/platform_compatibility.py", "Post-hoc platform check (excluded from composite)", "audit_required"))

    # Evaluator
    entries.append(build_artifact("evaluator/evaluator.py", "External evaluator (mode-gated)", "forbidden"))

    # Data
    entries.append(build_artifact("pipeline/data_sources/MANIFEST.md", "Data source provenance documentation", "audit_required"))
    entries.append(build_artifact("pipeline/data_sources/SNAPSHOT_HASHES.txt", "SHA256 manifest of cached snapshots", "forbidden"))

    # Scripts
    entries.append(build_artifact("scripts/scan_target_leakage.sh", "Source-code target-name scanner", "forbidden"))
    entries.append(build_artifact("scripts/verify_methodology_lock.sh", "Lock manifest verifier", "forbidden"))
    entries.append(build_artifact("scripts/scan_api_calls.sh", "Live API call audit (best-effort)", "audit_required"))
    entries.append(build_artifact("scripts/preflight.sh", "Loop-start environment check", "audit_required"))
    entries.append(build_artifact("scripts/canonicalize_output.py", "Reproducibility canonicalizer", "forbidden"))
    entries.append(build_artifact("scripts/loop_orchestrator.sh", "Round-lifecycle orchestrator", "audit_required"))
    entries.append(build_artifact("scripts/build_snapshot_manifest.sh", "Snapshot SHA256 manifest builder", "audit_required"))

    out = {
        "schema_version": "1.0",
        "lock_tag": "v1.0-methodology-locked",
        "note": (
            "This manifest is the SHA256-pinned methodology contract at lock time. "
            "Artifacts marked 'forbidden' must NEVER change in Phase β. "
            "Artifacts marked 'audit_required' may change in Phase β only with a "
            "documented engineering_audit_note.md endorsed by Codex (per AC-1.2). "
            "Verify with scripts/verify_methodology_lock.sh."
        ),
        "artifacts": sorted(entries, key=lambda e: e["path"]),
    }

    output_path = REPO_ROOT / "pipeline" / "LOCKED_ARTIFACTS.json"
    output_path.write_text(json.dumps(out, indent=2, sort_keys=True))
    n_forbidden = sum(1 for e in entries if e.get("mutability") == "forbidden")
    n_audit = sum(1 for e in entries if e.get("mutability") == "audit_required")
    n_missing = sum(1 for e in entries if e.get("status") == "MISSING_AT_LOCK_TIME")
    print(f"build_lock_manifest: wrote {output_path}")
    print(f"  artifacts: {len(entries)} total, {n_forbidden} forbidden, {n_audit} audit_required, {n_missing} missing")
    return 0 if n_missing == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
