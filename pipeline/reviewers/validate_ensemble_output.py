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
    elif "MOCK_STUB" not in mode:
        # Real-mode: require all six personas + per-persona structure
        per = doc.get("per_persona", {})
        missing = REQUIRED_PERSONAS - set(per.keys())
        if missing:
            errors.append(f"missing personas: {missing}")
        for p, body in per.items():
            if not isinstance(body, dict):
                errors.append(f"persona {p} body is not an object")

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
