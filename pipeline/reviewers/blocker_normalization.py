#!/usr/bin/env python3
"""Shared reviewer-blocker normalization (AC-5).

Used by run_ensemble.sh in BOTH regular and deferred modes to populate the
top-level `blockers_remaining` list. Also used by validate_ensemble_output.py
to enforce that propagation honestly reflects per-persona parsed critiques.

Rules (per Codex R8 required-implementation plan):
- Severity comparison is case-insensitive. "blocker", "BLOCKER", "Blocker" all count.
- String critiques become structured blockers only when the string itself contains
  the token "blocker" (case-insensitive); summary is the string itself.
- Null / "None" / empty / whitespace-only summaries do NOT yield a blocker entry.
- Every emitted blocker carries persona, normalized lower-case severity="blocker",
  and a non-empty trimmed summary.
"""
from __future__ import annotations
from typing import Any


_FALSE_SUMMARY_TOKENS = {"none", "null", "n/a", "na", "tbd", ""}


def _is_real_summary(s: Any) -> bool:
    if not isinstance(s, str):
        return False
    t = s.strip()
    if not t:
        return False
    if t.lower() in _FALSE_SUMMARY_TOKENS:
        return False
    return True


def normalize_blockers(per_persona: dict) -> list[dict]:
    """Return the flat list of real blocker entries, one per critique."""
    out: list[dict] = []
    for p_name, p_body in (per_persona or {}).items():
        if not isinstance(p_body, dict):
            continue
        critiques = p_body.get("critiques", []) or []
        if not isinstance(critiques, list):
            continue
        for c in critiques:
            if isinstance(c, dict):
                sev = str(c.get("severity", "")).strip().lower()
                if sev != "blocker":
                    continue
                summary = c.get("summary", "")
                if not _is_real_summary(summary):
                    continue
                out.append({
                    "persona": p_name,
                    "severity": "blocker",
                    "summary": summary.strip(),
                })
            elif isinstance(c, str):
                if "blocker" not in c.lower():
                    continue
                if not _is_real_summary(c):
                    continue
                out.append({
                    "persona": p_name,
                    "severity": "blocker",
                    "summary": c.strip(),
                })
    return out


def real_blocker_count(per_persona: dict) -> int:
    return len(normalize_blockers(per_persona))


if __name__ == "__main__":
    import argparse, json, sys
    ap = argparse.ArgumentParser()
    ap.add_argument("verdict_json", help="path to reviewer_ensemble_verdict.json")
    args = ap.parse_args()
    doc = json.loads(open(args.verdict_json).read())
    norm = normalize_blockers(doc.get("per_persona", {}))
    print(json.dumps({"normalized_blockers_count": len(norm), "blockers": norm}, indent=2))
    sys.exit(0)
