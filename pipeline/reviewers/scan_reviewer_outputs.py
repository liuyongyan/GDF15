#!/usr/bin/env python3
"""Scan reviewer outputs for forbidden target-name mentions.

Per AC-5 negative test: reviewer outputs that reference forbidden gene names
trigger a warning (Phase α) or blocker (Phase β).
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: scan_reviewer_outputs.py <verdict_json> [--phase=alpha|beta]", file=sys.stderr)
        return 2

    path = Path(argv[1])
    phase = "alpha"
    for a in argv[2:]:
        if a.startswith("--phase="):
            phase = a.split("=", 1)[1]

    forbidden_path = Path(__file__).resolve().parent / "FORBIDDEN_TARGET_NAMES.txt"
    if not forbidden_path.exists():
        print(f"scan_reviewer_outputs: ERROR - {forbidden_path} not found", file=sys.stderr)
        return 1

    forbidden = [ln.strip() for ln in forbidden_path.read_text().splitlines() if ln.strip()]
    pattern = re.compile("|".join(re.escape(n) for n in forbidden), re.IGNORECASE)

    text = path.read_text()
    hits = pattern.findall(text)
    if hits:
        print(f"scan_reviewer_outputs: {len(hits)} forbidden-name hit(s) in {path}: {sorted(set(hits))}")
        if phase == "beta":
            print("scan_reviewer_outputs: BLOCKER (Phase β)", file=sys.stderr)
            return 1
        else:
            print("scan_reviewer_outputs: WARNING (Phase α — non-blocking)", file=sys.stderr)
            return 0
    print("scan_reviewer_outputs: PASS - no forbidden names")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
