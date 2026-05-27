#!/usr/bin/env python3
"""Shared reviewer-blocker normalization (AC-5).

Used by run_ensemble.sh in BOTH regular and deferred modes to populate the
top-level `blockers_remaining` list. Also used by validate_ensemble_output.py
to enforce IDENTITY-LEVEL equivalence (every real blocker must appear in the
propagated list; not just count).

Round 10 schema robustness: the six personas emit critique entries in several
shapes in practice. Normalization handles each without dropping real blockers.

Schemas observed in real LLM verdicts:
- canonical dict: severity="blocker", summary="…"
- R3 shape:       severity="blocker", critique="…"  (text under `critique`, not `summary`)
- R4 shape:       blocker=true,        assessment="…"  (boolean flag, text under `assessment`)
- R5/R6 shape:    list of strings; treat strings as blockers IFF
                  per-persona `blockers_count > 0` AND len(strings) == blockers_count

Common rules:
- Dict is BLOCKER when severity (case-insensitive trim) == "blocker"
  OR blocker ∈ {True, "true", "yes", "blocker"}.
- Extract text from the first non-placeholder non-empty field among:
  summary, critique, assessment, detail, text, description, recommendation.
- Placeholder summaries ("None", "null", "n/a", "tbd", empty, whitespace) → drop.
- Every emitted blocker carries persona, normalized lower-case severity="blocker",
  a non-empty trimmed `summary`, and a stable `summary_hash` (SHA1 of normalized
  summary) for identity comparison.
"""
from __future__ import annotations
import hashlib
import re
from typing import Any


_FALSE_SUMMARY_TOKENS = {"none", "null", "n/a", "na", "tbd", ""}
_TEXT_FIELDS = ("summary", "critique", "assessment", "detail", "text", "description", "recommendation")
_BLOCKER_FLAG_TRUTHY = {True, "true", "yes", "blocker", "True", "Yes", "BLOCKER"}


def _normalize_summary(s: str) -> str:
    """Collapse whitespace and lowercase for identity comparison."""
    return re.sub(r"\s+", " ", s.strip()).lower()


def _summary_hash(s: str) -> str:
    return hashlib.sha1(_normalize_summary(s).encode("utf-8")).hexdigest()[:16]


def _is_real_summary(s: Any) -> bool:
    if not isinstance(s, str):
        return False
    t = s.strip()
    if not t:
        return False
    if t.lower() in _FALSE_SUMMARY_TOKENS:
        return False
    return True


def _extract_text(d: dict) -> str | None:
    for k in _TEXT_FIELDS:
        v = d.get(k)
        if _is_real_summary(v):
            return v.strip()
    return None


def _is_dict_blocker(d: dict) -> bool:
    sev = str(d.get("severity", "")).strip().lower()
    if sev == "blocker":
        return True
    blk = d.get("blocker")
    if blk in _BLOCKER_FLAG_TRUTHY:
        return True
    if isinstance(blk, str) and blk.strip().lower() in {"true", "yes", "blocker"}:
        return True
    return False


def normalize_blockers(per_persona: dict) -> list[dict]:
    """Return the flat list of real blocker entries, one per critique.

    Each entry has: persona, severity="blocker", summary, summary_hash.
    """
    out: list[dict] = []
    for p_name, p_body in (per_persona or {}).items():
        if not isinstance(p_body, dict):
            continue
        critiques = p_body.get("critiques", []) or []
        if not isinstance(critiques, list):
            continue

        # Pass 1: dict critiques with explicit blocker marker
        for c in critiques:
            if not isinstance(c, dict):
                continue
            if not _is_dict_blocker(c):
                continue
            text = _extract_text(c)
            if not text:
                continue
            out.append({
                "persona": p_name,
                "severity": "blocker",
                "summary": text,
                "summary_hash": _summary_hash(text),
            })

        # Pass 2: string critiques. Treat strings as blockers only when persona's
        # parsed blockers_count > 0 AND len(string critiques) == blockers_count
        # (otherwise the strings are too ambiguous to bind to "blocker" specifically).
        try:
            bc = int(p_body.get("blockers_count", 0) or 0)
        except (TypeError, ValueError):
            bc = 0
        string_critiques = [c for c in critiques if isinstance(c, str) and _is_real_summary(c)]
        if bc > 0 and len(string_critiques) == bc:
            for s in string_critiques:
                t = s.strip()
                out.append({
                    "persona": p_name,
                    "severity": "blocker",
                    "summary": t,
                    "summary_hash": _summary_hash(t),
                })

    return out


def real_blocker_count(per_persona: dict) -> int:
    return len(normalize_blockers(per_persona))


def identity_set(blockers: list[dict]) -> set[tuple[str, str]]:
    """Compute the (persona, summary_hash) identity set used for propagation checks."""
    out: set[tuple[str, str]] = set()
    for b in blockers or []:
        if not isinstance(b, dict):
            continue
        persona = b.get("persona", "")
        summary = b.get("summary", "")
        if not summary:
            continue
        sh = b.get("summary_hash") or _summary_hash(summary)
        out.add((persona, sh))
    return out


if __name__ == "__main__":
    import argparse, json, sys
    ap = argparse.ArgumentParser()
    ap.add_argument("verdict_json", help="path to reviewer_ensemble_verdict.json")
    args = ap.parse_args()
    doc = json.loads(open(args.verdict_json).read())
    norm = normalize_blockers(doc.get("per_persona", {}))
    print(json.dumps({"normalized_blockers_count": len(norm), "blockers": norm}, indent=2))
    sys.exit(0)
