#!/usr/bin/env python3
"""Run-local adjudication binding (AC-11 R2 fix).

Loads pipeline/audits/reviewer_blocker_adjudications.json (the canonical machine-
readable source maintained by humans across rounds) and returns the subset of
adjudications that match a given verdict's propagated blockers.

Matching rules (strict):
- Primary: (persona, summary_hash) when both sides have a non-null summary_hash.
- Fallback: (persona, round) ONLY for adjudications that explicitly declare
  summary_hash=null AND round=N matches the verdict's round. This handles
  historical entries where the original blocker text was lost (e.g., ADJ-001
  whose source verdict was overwritten by a cache regeneration).

The returned list is what should be written into verdict.meta_review.adjudications
BEFORE redaction and BEFORE validation, so the run-local artifact carries its own
adjudication state and downstream consumers (walkthrough, R figures, validator)
have a single trusted source.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CANONICAL_JSON = REPO_ROOT / "pipeline" / "audits" / "reviewer_blocker_adjudications.json"


def _validate_entry(e: dict) -> bool:
    required = {"adjudication_id", "round", "persona", "disposition"}
    missing = required - set(e.keys())
    if missing:
        print(f"adjudication_binding: WARN entry missing required fields: {sorted(missing)}",
              file=sys.stderr)
        return False
    if e["disposition"] not in {"REBUTTED", "RESOLVED_BY_REVISION", "ACCEPTED_LIMITATION"}:
        print(f"adjudication_binding: WARN entry {e.get('adjudication_id')} has invalid disposition "
              f"{e.get('disposition')!r}", file=sys.stderr)
        return False
    return True


def _load_canonical() -> list[dict]:
    if not CANONICAL_JSON.exists():
        return []
    try:
        doc = json.loads(CANONICAL_JSON.read_text())
    except json.JSONDecodeError as ex:
        print(f"adjudication_binding: ERROR malformed canonical JSON: {ex}", file=sys.stderr)
        return []
    entries = doc.get("adjudications", []) or []
    return [e for e in entries if isinstance(e, dict) and _validate_entry(e)]


def bind_adjudications(per_persona: dict, blockers_remaining: list, round_num: int) -> list[dict]:
    """Return the subset of canonical adjudications matching the verdict's propagated blockers.

    Each returned dict is a copy of the canonical entry, suitable for embedding directly
    into verdict.meta_review.adjudications.
    """
    canonical = _load_canonical()
    if not canonical:
        return []

    out: list[dict] = []
    seen_keys: set = set()  # dedupe by adjudication_id

    # Build identity sets from the verdict's propagated blockers
    propagated = blockers_remaining or []
    propagated_hashes: set = set()
    propagated_personas_for_round: set = set()
    for b in propagated:
        if not isinstance(b, dict):
            continue
        h = b.get("summary_hash")
        p = b.get("persona")
        if h:
            propagated_hashes.add((p, h))
        if p:
            propagated_personas_for_round.add(p)

    for adj in canonical:
        adj_id = adj.get("adjudication_id")
        if adj_id in seen_keys:
            continue
        adj_persona = adj.get("persona")
        adj_hash = adj.get("blocker_summary_hash")
        adj_round = adj.get("round")

        matched = False
        # Primary match: (persona, summary_hash)
        if adj_hash and (adj_persona, adj_hash) in propagated_hashes:
            matched = True
        # Fallback: (persona, round) for explicitly hashless entries
        elif adj_hash is None and adj_round == round_num and adj_persona in propagated_personas_for_round:
            matched = True

        if matched:
            out.append(dict(adj))  # shallow copy
            seen_keys.add(adj_id)

    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("verdict_json", help="path to runs/round_N/reviewer_ensemble_verdict.json")
    args = ap.parse_args()
    v = json.loads(Path(args.verdict_json).read_text())
    matched = bind_adjudications(
        per_persona=v.get("per_persona", {}),
        blockers_remaining=v.get("blockers_remaining", []),
        round_num=int(v.get("round", 0)),
    )
    print(json.dumps({"matched_count": len(matched), "adjudications": matched}, indent=2))
    sys.exit(0)
