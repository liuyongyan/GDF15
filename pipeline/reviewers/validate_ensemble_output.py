#!/usr/bin/env python3
"""Validate reviewer_ensemble_verdict.json schema."""
from __future__ import annotations
import json
import sys
from pathlib import Path


REQUIRED_PERSONAS = {
    "R1_molecular_biologist",
    "R2_clinical_translator",
    "R3_geneticist_biostatistician",
    "R4_pharmacologist",
    "R5_ai_methods_reviewer",
    "R6_editor",
}


def lock_tag_exists() -> bool:
    import subprocess
    try:
        r = subprocess.run(
            ["git", "rev-parse", "refs/tags/v1.0-methodology-locked"],
            capture_output=True, text=True, check=False,
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.SubprocessError):
        return False


REQUIRED_DEFERRED_FIELDS = {"status", "reason", "affected_personas", "affected_backbones", "remediation"}
REQUIRED_PER_PERSONA_FIELDS_REAL = {"persona", "raw_text", "raw_text_sha1", "parsed_json_present", "blockers_count", "critiques"}


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: validate_ensemble_output.py <verdict_json>", file=sys.stderr)
        return 2
    path = Path(argv[1])
    if not path.exists():
        print(f"validate_ensemble_output: ERROR - file not found: {path}", file=sys.stderr)
        return 1
    try:
        doc = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"validate_ensemble_output: ERROR - malformed JSON: {e}", file=sys.stderr)
        return 1

    errors: list[str] = []
    mode = doc.get("mode", "REGULAR")
    status = doc.get("status", "")

    # MOCK_STUB is only acceptable BEFORE methodology lock.
    if "MOCK_STUB" in mode:
        if lock_tag_exists():
            errors.append(
                "MOCK_STUB reviewer verdict is not acceptable after methodology lock. "
                "Real LLM invocations are required."
            )
        else:
            print(f"validate_ensemble_output: NOTE - {mode} accepted pre-lock; must be replaced before Phase β.")

    deferred = status == "REVIEWER_DEFERRED" or mode.startswith("REVIEWER_DEFERRED")

    if deferred:
        # REVIEWER_DEFERRED schema: status, reason, affected_personas, affected_backbones, remediation
        missing_fields = REQUIRED_DEFERRED_FIELDS - set(doc.keys())
        if missing_fields:
            errors.append(f"REVIEWER_DEFERRED missing required fields: {sorted(missing_fields)}")
        if doc.get("reason") and not isinstance(doc["reason"], str):
            errors.append("'reason' must be a string")
        if doc.get("reason") == "":
            errors.append("'reason' must be non-empty")
        if not isinstance(doc.get("affected_personas", []), list):
            errors.append("'affected_personas' must be a list")
        if not isinstance(doc.get("affected_backbones", []), list):
            errors.append("'affected_backbones' must be a list")
        if doc.get("remediation") and not isinstance(doc["remediation"], str):
            errors.append("'remediation' must be a string")
        # Codex R6/R7: enforce per-persona parsed-field structural honesty in deferred mode
        per = doc.get("per_persona", {}) or {}
        total_parsed_blockers = 0
        for p_name, p_body in per.items():
            if not isinstance(p_body, dict):
                continue
            if p_body.get("missing") or p_body.get("status") in {"BOTH_BACKBONES_FAILED", "MISSING_PROMPT"}:
                continue
            field_gap = REQUIRED_PER_PERSONA_FIELDS_REAL - set(p_body.keys())
            if field_gap:
                errors.append(f"deferred-mode persona {p_name} missing parsed fields: {sorted(field_gap)}")
            try:
                total_parsed_blockers += int(p_body.get("blockers_count", 0) or 0)
            except (TypeError, ValueError):
                pass
        if total_parsed_blockers > 0 and not doc.get("blockers_remaining"):
            errors.append(
                f"deferred-mode verdict has {total_parsed_blockers} parsed blocker(s) across personas "
                f"but top-level blockers_remaining is empty"
            )
    elif "MOCK_STUB" not in mode:
        # Real-mode: require all six personas + per-persona structure with parsed evidence
        per = doc.get("per_persona", {})
        missing = REQUIRED_PERSONAS - set(per.keys())
        if missing:
            errors.append(f"missing personas: {missing}")
        for p, body in per.items():
            if not isinstance(body, dict):
                errors.append(f"persona {p} body is not an object")
                continue
            if body.get("missing"):
                errors.append(f"persona {p} marked missing in real-mode verdict")
                continue
            field_gap = REQUIRED_PER_PERSONA_FIELDS_REAL - set(body.keys())
            if field_gap:
                errors.append(f"persona {p} missing required fields: {sorted(field_gap)}")

    if "meta_review" not in doc:
        errors.append("missing meta_review")
    if "blockers_remaining" not in doc:
        errors.append("missing blockers_remaining array")

    if errors:
        print(f"validate_ensemble_output: FAIL - {len(errors)} error(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"validate_ensemble_output: PASS - {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
