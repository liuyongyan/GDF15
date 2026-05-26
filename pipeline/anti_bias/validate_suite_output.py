#!/usr/bin/env python3
"""Validate that all 5 anti-bias mechanisms have run and produced expected outputs."""
from __future__ import annotations
import json
import sys
from pathlib import Path


REQUIRED_FILES = [
    "_results_loo.json",
    "_results_nc.json",
    "_results_lit_blind.json",
    "_results_mr.json",
    "_results_perm.json",
]


def main() -> int:
    base = Path(__file__).resolve().parent
    errors = []
    for fn in REQUIRED_FILES:
        p = base / fn
        if not p.exists():
            errors.append(f"missing {fn}")
            continue
        try:
            doc = json.loads(p.read_text())
        except json.JSONDecodeError:
            errors.append(f"malformed JSON in {fn}")
            continue
        if "mechanism" not in doc:
            errors.append(f"{fn} missing 'mechanism' field")
        if fn == "_results_mr.json":
            if doc.get("status") == "OPTIONAL_SKIPPED" and not doc.get("reason"):
                errors.append("MR OPTIONAL_SKIPPED but no 'reason' field")

    if errors:
        print(f"validate_suite_output: FAIL - {len(errors)} error(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("validate_suite_output: PASS - all 5 anti-bias mechanism outputs present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
