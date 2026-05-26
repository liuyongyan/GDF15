#!/usr/bin/env python3
"""Canonicalize a Pipeline output JSON for reproducibility comparison.

Strips runtime-dependent fields (timestamps, git SHAs that depend on prior commits),
sorts keys, and pretty-prints. The result of canonicalize on two independent
runs of the same Pipeline (on the same cached data) should be byte-identical.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path


# Fields to exclude (their presence/value can vary across runs without affecting correctness)
EXCLUDE_TOPLEVEL = {"pre_registration_hash"}
EXCLUDE_FROM_REVIEWER = {"round", "mode"}


def canonicalize(doc: dict) -> dict:
    out = {}
    for k, v in doc.items():
        if k in EXCLUDE_TOPLEVEL:
            continue
        if k == "reviewer_ensemble_verdict" and isinstance(v, dict):
            inner = {kk: vv for kk, vv in v.items() if kk not in EXCLUDE_FROM_REVIEWER}
            out[k] = inner
        else:
            out[k] = v
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: canonicalize_output.py <input.json> [<output.json>]", file=sys.stderr)
        return 2
    inp = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else inp.with_suffix(".canonical.json")
    doc = json.loads(inp.read_text())
    canon = canonicalize(doc)
    out.write_text(json.dumps(canon, indent=2, sort_keys=True))
    print(f"canonicalize_output: wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
