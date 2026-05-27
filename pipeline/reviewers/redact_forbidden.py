#!/usr/bin/env python3
"""Redact forbidden target identifiers from reviewer prose.

Used by run_ensemble.sh BEFORE writing the verdict JSON to disk.
Replaces forbidden names with the placeholder `[REDACTED_TARGET]` in:
  - per_persona.*.raw_text
  - per_persona.*.critiques[].summary/detail (when dict)
  - per_persona.*.global_methodology_notes[]
  - per_persona.*.pipeline_methodology_critique
  - meta_review.cross_reviewer_agreement_summary
  - meta_review.pipeline_methodology_concerns[]
  - meta_review.consensus_blockers[].summary
  - meta_review.single_reviewer_blockers[].summary
  - blockers_remaining[].summary
  - reason / remediation

Hash of the redacted text is recomputed (raw_text_sha1) so reproducibility
remains anchored to the redacted version.
"""
from __future__ import annotations
import hashlib
import json
import re
import sys
from pathlib import Path


PLACEHOLDER = "[REDACTED_TARGET]"


def redact_text(text: str, pattern: re.Pattern) -> str:
    return pattern.sub(PLACEHOLDER, text)


def redact_inplace(doc: dict, pattern: re.Pattern) -> dict:
    # Top-level prose
    if isinstance(doc.get("reason"), str):
        doc["reason"] = redact_text(doc["reason"], pattern)
    if isinstance(doc.get("remediation"), str):
        doc["remediation"] = redact_text(doc["remediation"], pattern)
    # blockers_remaining
    for blk in doc.get("blockers_remaining", []) or []:
        if isinstance(blk, dict) and isinstance(blk.get("summary"), str):
            blk["summary"] = redact_text(blk["summary"], pattern)
    # meta_review
    meta = doc.get("meta_review", {}) or {}
    if isinstance(meta, dict):
        if isinstance(meta.get("cross_reviewer_agreement_summary"), str):
            meta["cross_reviewer_agreement_summary"] = redact_text(
                meta["cross_reviewer_agreement_summary"], pattern)
        meta["pipeline_methodology_concerns"] = [
            redact_text(c, pattern) if isinstance(c, str) else c
            for c in meta.get("pipeline_methodology_concerns", []) or []
        ]
        for blist_key in ("consensus_blockers", "single_reviewer_blockers"):
            for blk in meta.get(blist_key, []) or []:
                if isinstance(blk, dict) and isinstance(blk.get("summary"), str):
                    blk["summary"] = redact_text(blk["summary"], pattern)
    # per_persona
    per = doc.get("per_persona", {}) or {}
    if isinstance(per, dict):
        for body in per.values():
            if not isinstance(body, dict):
                continue
            if isinstance(body.get("raw_text"), str):
                body["raw_text"] = redact_text(body["raw_text"], pattern)
                body["raw_text_sha1"] = hashlib.sha1(body["raw_text"].encode("utf-8")).hexdigest()
            if isinstance(body.get("pipeline_methodology_critique"), str):
                body["pipeline_methodology_critique"] = redact_text(
                    body["pipeline_methodology_critique"], pattern)
            body["global_methodology_notes"] = [
                redact_text(n, pattern) if isinstance(n, str) else n
                for n in body.get("global_methodology_notes", []) or []
            ]
            for crit in body.get("critiques", []) or []:
                if isinstance(crit, dict):
                    for k in ("summary", "detail"):
                        if isinstance(crit.get(k), str):
                            crit[k] = redact_text(crit[k], pattern)
    return doc


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: redact_forbidden.py <verdict_json>", file=sys.stderr)
        return 2
    path = Path(argv[1])
    forbidden_path = Path(__file__).resolve().parent / "FORBIDDEN_TARGET_NAMES.txt"
    forbidden = [ln.strip() for ln in forbidden_path.read_text().splitlines() if ln.strip()]
    pattern = re.compile(r"\b(" + "|".join(re.escape(n) for n in forbidden) + r")\b", re.IGNORECASE)
    doc = json.loads(path.read_text())
    redact_inplace(doc, pattern)
    path.write_text(json.dumps(doc, indent=2, sort_keys=True))
    print(f"redact_forbidden: redacted {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
