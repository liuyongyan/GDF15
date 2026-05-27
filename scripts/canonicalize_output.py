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
# Per AC-5, reviewer ensemble output is allowed to be non-deterministic (real LLM responses
# vary across calls). For byte-comparable AC-9 reproducibility, the entire reviewer block is
# excluded along with the runtime-only top-level fields below. See CANONICAL_EXCLUSIONS.md.
EXCLUDE_TOPLEVEL = {"pre_registration_hash", "round", "reviewer_ensemble_verdict"}


def canonicalize(doc: dict) -> dict:
    return {k: v for k, v in doc.items() if k not in EXCLUDE_TOPLEVEL}


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: canonicalize_output.py <input.json> [<output.json>|-]", file=sys.stderr)
        return 2
    inp = Path(sys.argv[1])
    doc = json.loads(inp.read_text())
    canon = canonicalize(doc)
    canon_text = json.dumps(canon, indent=2, sort_keys=True)
    if len(sys.argv) > 2 and sys.argv[2] == "-":
        # stdout mode (for diff use)
        sys.stdout.write(canon_text + "\n")
        return 0
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else inp.with_suffix(".canonical.json")
    out.write_text(canon_text)
    print(f"canonicalize_output: wrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
