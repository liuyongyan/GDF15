#!/usr/bin/env python3
"""Scan reviewer-AUTHORED PROSE for forbidden target-name mentions.

Per AC-5 negative test: forbidden gene names in reviewer prose trigger a warning
(Phase α) or blocker (Phase β).

This scanner is narrowly scoped to reviewer-authored prose fields, excluding
wrapper bookkeeping (file paths, hashes, statuses, schema versions) which can
legitimately contain target identifiers as part of audit metadata. Per Codex
Round 6 review, the previous implementation read the whole JSON serialization
and conflated reviewer prose with wrapper metadata.

Scoped fields scanned:
  - per_persona.*.raw_text                          (reviewer's verbatim response body)
  - per_persona.*.critiques[].summary/detail        (parsed critique prose)
  - per_persona.*.global_methodology_notes[]        (parsed notes)
  - per_persona.*.pipeline_methodology_critique     (parsed)
  - meta_review.cross_reviewer_agreement_summary    (aggregator prose)
  - meta_review.pipeline_methodology_concerns[]     (aggregator prose)
  - meta_review.consensus_blockers[].summary        (aggregator prose)
  - meta_review.single_reviewer_blockers[].summary  (aggregator prose)
  - blockers_remaining[].summary                    (top-level prose)
  - reason                                          (deferral reason prose)
  - remediation                                     (deferral remediation prose)

Excluded by design:
  - file paths, cache paths, prompt/input hashes
  - status fields, mode, schema_version, round
  - persona ids (R1_molecular_biologist etc.) — these are not reviewer prose
  - affected_personas / affected_backbones lists — these reference structures, not prose
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path


def collect_reviewer_prose(doc: dict) -> list[tuple[str, str]]:
    """Walk the verdict JSON and return (field_path, prose_text) for reviewer-authored fields."""
    out: list[tuple[str, str]] = []

    # Top-level prose
    if isinstance(doc.get("reason"), str):
        out.append(("$.reason", doc["reason"]))
    if isinstance(doc.get("remediation"), str):
        out.append(("$.remediation", doc["remediation"]))

    # blockers_remaining
    for i, blk in enumerate(doc.get("blockers_remaining", []) or []):
        if isinstance(blk, dict):
            if isinstance(blk.get("summary"), str):
                out.append((f"$.blockers_remaining[{i}].summary", blk["summary"]))
        elif isinstance(blk, str):
            out.append((f"$.blockers_remaining[{i}]", blk))

    # meta_review prose
    meta = doc.get("meta_review", {}) or {}
    if isinstance(meta, dict):
        if isinstance(meta.get("cross_reviewer_agreement_summary"), str):
            out.append(("$.meta_review.cross_reviewer_agreement_summary",
                        meta["cross_reviewer_agreement_summary"]))
        for i, concern in enumerate(meta.get("pipeline_methodology_concerns", []) or []):
            if isinstance(concern, str):
                out.append((f"$.meta_review.pipeline_methodology_concerns[{i}]", concern))
        for blist_key in ("consensus_blockers", "single_reviewer_blockers"):
            for i, blk in enumerate(meta.get(blist_key, []) or []):
                if isinstance(blk, dict) and isinstance(blk.get("summary"), str):
                    out.append((f"$.meta_review.{blist_key}[{i}].summary", blk["summary"]))
                elif isinstance(blk, str):
                    out.append((f"$.meta_review.{blist_key}[{i}]", blk))

    # per_persona prose
    per = doc.get("per_persona", {}) or {}
    if isinstance(per, dict):
        for persona, body in per.items():
            if not isinstance(body, dict):
                continue
            if isinstance(body.get("raw_text"), str):
                out.append((f"$.per_persona.{persona}.raw_text", body["raw_text"]))
            if isinstance(body.get("pipeline_methodology_critique"), str):
                out.append((f"$.per_persona.{persona}.pipeline_methodology_critique",
                            body["pipeline_methodology_critique"]))
            for i, note in enumerate(body.get("global_methodology_notes", []) or []):
                if isinstance(note, str):
                    out.append((f"$.per_persona.{persona}.global_methodology_notes[{i}]", note))
            for i, crit in enumerate(body.get("critiques", []) or []):
                if isinstance(crit, dict):
                    for k in ("summary", "detail"):
                        v = crit.get(k)
                        if isinstance(v, str):
                            out.append((f"$.per_persona.{persona}.critiques[{i}].{k}", v))
                elif isinstance(crit, str):
                    out.append((f"$.per_persona.{persona}.critiques[{i}]", crit))

    return out


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
    pattern = re.compile(r"\b(" + "|".join(re.escape(n) for n in forbidden) + r")\b", re.IGNORECASE)

    try:
        doc = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"scan_reviewer_outputs: ERROR - malformed JSON: {e}", file=sys.stderr)
        return 1

    prose_fields = collect_reviewer_prose(doc)
    hits: list[tuple[str, list[str]]] = []
    for field_path, prose in prose_fields:
        matches = pattern.findall(prose)
        if matches:
            hits.append((field_path, sorted(set(matches))))

    if hits:
        print(f"scan_reviewer_outputs: {len(hits)} reviewer-prose field(s) contain forbidden names:")
        for field_path, matches in hits:
            print(f"  {field_path}: {matches}")
        if phase == "beta":
            print("scan_reviewer_outputs: BLOCKER (Phase β)", file=sys.stderr)
            return 1
        else:
            print("scan_reviewer_outputs: WARNING (Phase α — non-blocking)", file=sys.stderr)
            return 0
    print(f"scan_reviewer_outputs: PASS - no forbidden names in {len(prose_fields)} reviewer-prose field(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
