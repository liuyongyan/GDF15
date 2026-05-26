#!/usr/bin/env python3
"""Validate pipeline/scoring/weights.json against constraints.

AC-4: weights sum to 1.0 (+/- 1e-6), no single weight > 0.40,
excluded_from_composite dimensions are not weighted.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path


def main() -> int:
    pipeline_root = Path(__file__).resolve().parent.parent
    weights_path = pipeline_root / "scoring" / "weights.json"
    dims_path = pipeline_root / "scoring" / "dimensions.json"

    if not weights_path.exists():
        print(f"validate_weights: ERROR - {weights_path} not found", file=sys.stderr)
        return 1
    if not dims_path.exists():
        print(f"validate_weights: ERROR - {dims_path} not found", file=sys.stderr)
        return 1

    weights_doc = json.loads(weights_path.read_text())
    dims_doc = json.loads(dims_path.read_text())

    weights = weights_doc.get("weights", {})
    excluded = set(weights_doc.get("excluded_from_composite", []))
    dim_excluded_in_dims = {
        d["id"] for d in dims_doc.get("dimensions", [])
        if d.get("excluded_from_composite")
    }

    errors = []

    # Sum check
    total = sum(weights.values())
    if abs(total - 1.0) > 1e-6:
        errors.append(f"weights sum to {total}, expected 1.0 +/- 1e-6")
    else:
        print(f"validate_weights: OK - weights sum to {total} (within tolerance)")

    # Max weight check
    for k, v in weights.items():
        if v > 0.40:
            errors.append(f"weight {k}={v} exceeds 0.40 maximum")
        if v < 0:
            errors.append(f"weight {k}={v} is negative")

    # Excluded dimensions must not appear in weights
    for ex in excluded:
        if ex in weights:
            errors.append(f"excluded dimension {ex} should not appear in weights map")

    # Consistency: excluded sets must match between dimensions.json and weights.json
    if excluded != dim_excluded_in_dims:
        errors.append(
            f"excluded_from_composite mismatch: weights.json={excluded}, dimensions.json={dim_excluded_in_dims}"
        )
    else:
        print(f"validate_weights: OK - excluded set consistent ({excluded})")

    # Every weighted dimension must exist in dimensions.json
    dim_ids = {d["id"] for d in dims_doc.get("dimensions", [])}
    for k in weights:
        if k not in dim_ids:
            errors.append(f"weight key {k} is not declared in dimensions.json")

    if errors:
        print(f"validate_weights: FAIL - {len(errors)} error(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("validate_weights: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
