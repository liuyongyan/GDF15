#!/usr/bin/env python3
"""Validate pipeline input JSON against AC-2 IO contract.

Required top-level fields (per draft §3.1):
  - question (string)
  - phenotype_profile_desired (object with at least one key)
  - indication_context (string)

Exit codes:
  0  - PASS
  1  - validation failure
  2  - file missing or unreadable
"""
from __future__ import annotations
import json
import sys
from pathlib import Path


REQUIRED_TOPLEVEL = ["question", "phenotype_profile_desired", "indication_context"]


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: validate_input.py <input.json>", file=sys.stderr)
        return 2

    path = Path(argv[1])
    if not path.exists():
        print(f"validate_input: ERROR - input file not found: {path}", file=sys.stderr)
        return 2

    try:
        doc = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        print(f"validate_input: ERROR - cannot parse {path}: {e}", file=sys.stderr)
        return 2

    errors: list[str] = []

    for k in REQUIRED_TOPLEVEL:
        if k not in doc:
            errors.append(f"missing required field: {k}")

    if "question" in doc and not isinstance(doc["question"], str):
        errors.append("'question' must be a string")
    if "question" in doc and not doc.get("question", "").strip():
        errors.append("'question' must be non-empty")

    if "phenotype_profile_desired" in doc:
        ppd = doc["phenotype_profile_desired"]
        if not isinstance(ppd, dict):
            errors.append("'phenotype_profile_desired' must be a JSON object")
        elif not ppd:
            errors.append("'phenotype_profile_desired' must contain at least one key")

    if "indication_context" in doc and not isinstance(doc["indication_context"], str):
        errors.append("'indication_context' must be a string")
    if "indication_context" in doc and not doc.get("indication_context", "").strip():
        errors.append("'indication_context' must be non-empty")

    if errors:
        print(f"validate_input: FAIL ({len(errors)} error(s)):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"validate_input: PASS ({path})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
