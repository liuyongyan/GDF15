#!/usr/bin/env python3
"""Validate reviewer_ensemble_verdict.json schema."""
from __future__ import annotations
import json
import sys
from pathlib import Path


REQUIRED_PERSONAS = {
    "R1_molecular_biologist",
    "R2_clinical_translator",
    "R3_geneticist_biostatistician",
    "R4_pharmacologist",
    "R5_ai_methods_reviewer",
    "R6_editor",
}


def lock_tag_exists() -> bool:
    import subprocess
    try:
        r = subprocess.run(
            ["git", "rev-parse", "refs/tags/v1.0-methodology-locked"],
            capture_output=True, text=True, check=False,
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.SubprocessError):
        return False


REQUIRED_DEFERRED_FIELDS = {"status", "reason", "affected_personas", "affected_backbones", "remediation"}
REQUIRED_PER_PERSONA_FIELDS_REAL = {
    "persona", "raw_text", "raw_text_sha1", "parsed_json_present",
    "blockers_count", "critiques",
    # AC-5 provenance fields (Round 9)
    "status", "backbone_used", "prompt_hash", "input_hash",
}


def _real_blocker_list(per_persona: dict) -> list:
    """Use the shared normalization routine — same logic the verdict-writer uses."""
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parent))
    from blocker_normalization import normalize_blockers
    return normalize_blockers(per_persona)


def _identity_set(blockers: list) -> set:
    """Use the shared identity helper for propagation-equivalence checks."""
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parent))
    from blocker_normalization import identity_set
    return identity_set(blockers)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: validate_ensemble_output.py <verdict_json>", file=sys.stderr)
        return 2
    path = Path(argv[1])
    if not path.exists():
        print(f"validate_ensemble_output: ERROR - file not found: {path}", file=sys.stderr)
        return 1
    try:
        doc = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"validate_ensemble_output: ERROR - malformed JSON: {e}", file=sys.stderr)
        return 1

    errors: list[str] = []
    mode = doc.get("mode", "REGULAR")
    status = doc.get("status", "")

    # MOCK_STUB is only acceptable BEFORE methodology lock.
    if "MOCK_STUB" in mode:
        if lock_tag_exists():
            errors.append(
                "MOCK_STUB reviewer verdict is not acceptable after methodology lock. "
                "Real LLM invocations are required."
            )
        else:
            print(f"validate_ensemble_output: NOTE - {mode} accepted pre-lock; must be replaced before Phase β.")

    deferred = status == "REVIEWER_DEFERRED" or mode.startswith("REVIEWER_DEFERRED")

    if deferred:
        # REVIEWER_DEFERRED schema: status, reason, affected_personas, affected_backbones, remediation
        missing_fields = REQUIRED_DEFERRED_FIELDS - set(doc.keys())
        if missing_fields:
            errors.append(f"REVIEWER_DEFERRED missing required fields: {sorted(missing_fields)}")
        if doc.get("reason") and not isinstance(doc["reason"], str):
            errors.append("'reason' must be a string")
        if doc.get("reason") == "":
            errors.append("'reason' must be non-empty")
        if not isinstance(doc.get("affected_personas", []), list):
            errors.append("'affected_personas' must be a list")
        if not isinstance(doc.get("affected_backbones", []), list):
            errors.append("'affected_backbones' must be a list")
        if doc.get("remediation") and not isinstance(doc["remediation"], str):
            errors.append("'remediation' must be a string")
        # Codex R6/R7: enforce per-persona parsed-field structural honesty in deferred mode
        per = doc.get("per_persona", {}) or {}
        total_parsed_blockers = 0
        for p_name, p_body in per.items():
            if not isinstance(p_body, dict):
                continue
            if p_body.get("missing") or p_body.get("status") in {"BOTH_BACKBONES_FAILED", "MISSING_PROMPT"}:
                continue
            field_gap = REQUIRED_PER_PERSONA_FIELDS_REAL - set(p_body.keys())
            if field_gap:
                errors.append(f"deferred-mode persona {p_name} missing parsed fields: {sorted(field_gap)}")
            try:
                total_parsed_blockers += int(p_body.get("blockers_count", 0) or 0)
            except (TypeError, ValueError):
                pass
        # Shared identity invariant: every real blocker must appear in blockers_remaining.
        real_blockers = _real_blocker_list(per)
        propagated_ids = _identity_set(doc.get("blockers_remaining", []) or [])
        real_ids = _identity_set(real_blockers)
        missing_ids = real_ids - propagated_ids
        if missing_ids:
            errors.append(
                f"deferred-mode verdict drops {len(missing_ids)} real blocker(s) not present "
                f"in blockers_remaining (identity check): {sorted(missing_ids)[:3]}{'...' if len(missing_ids) > 3 else ''}"
            )
    elif "MOCK_STUB" not in mode:
        # Real (regular) mode: require all six personas + full provenance + honest blocker propagation
        per = doc.get("per_persona", {})
        missing = REQUIRED_PERSONAS - set(per.keys())
        if missing:
            errors.append(f"missing personas in regular-mode verdict: {sorted(missing)}")
        for p, body in per.items():
            if not isinstance(body, dict):
                errors.append(f"persona {p} body is not an object")
                continue
            if body.get("missing"):
                errors.append(f"persona {p} marked missing in real-mode verdict")
                continue
            field_gap = REQUIRED_PER_PERSONA_FIELDS_REAL - set(body.keys())
            if field_gap:
                errors.append(f"persona {p} missing required fields: {sorted(field_gap)}")
        # Same shared identity invariant: every real blocker must appear in blockers_remaining.
        real_blockers = _real_blocker_list(per)
        propagated_ids = _identity_set(doc.get("blockers_remaining", []) or [])
        real_ids = _identity_set(real_blockers)
        missing_ids = real_ids - propagated_ids
        if missing_ids:
            errors.append(
                f"regular-mode verdict drops {len(missing_ids)} real blocker(s) not present "
                f"in blockers_remaining (identity check): {sorted(missing_ids)[:3]}{'...' if len(missing_ids) > 3 else ''}"
            )
        # Round 11 hardening: post-lock regular-mode rejects count-vs-critique
        # contradictions UNLESS an explicit adjudication entry exists in
        # meta_review.unbound_blockers[persona]. This stops the verdict from claiming
        # blockers exist (count > 0) without either propagating them or recording why
        # they should be ignored.
        unbound = (doc.get("meta_review", {}) or {}).get("unbound_blockers", {}) or {}
        is_post_lock = lock_tag_exists()
        for p_name, body in per.items():
            if not isinstance(body, dict):
                continue
            try:
                bc = int(body.get("blockers_count", 0) or 0)
            except (TypeError, ValueError):
                continue
            if bc <= 0:
                continue
            persona_real = [b for b in real_blockers if b["persona"] == p_name]
            if persona_real:
                continue
            msg = (
                f"persona {p_name} reports blockers_count={bc} but no real blocker survived "
                f"normalization (placeholder summary or non-blocker severity)"
            )
            if is_post_lock and not isinstance(unbound.get(p_name), (dict, str)):
                errors.append(
                    msg + f"; post-lock requires an entry in meta_review.unbound_blockers[\"{p_name}\"] "
                    f"explaining adjudication"
                )
            else:
                print(f"validate_ensemble_output: WARN - {msg}", file=sys.stderr)

    if "meta_review" not in doc:
        errors.append("missing meta_review")
    if "blockers_remaining" not in doc:
        errors.append("missing blockers_remaining array")

    # AC-11 R2: if a canonical adjudication exists for any propagated blocker, the verdict's
    # meta_review.adjudications MUST include the matching entry (run-local binding, not sidecar).
    if "blockers_remaining" in doc:
        try:
            import sys as _sys
            from pathlib import Path as _Path
            _sys.path.insert(0, str(_Path(__file__).resolve().parent))
            from adjudication_binding import bind_adjudications
            expected = bind_adjudications(
                per_persona=doc.get("per_persona", {}),
                blockers_remaining=doc.get("blockers_remaining", []),
                round_num=int(doc.get("round", 0)),
            )
            verdict_adj = doc.get("meta_review", {}).get("adjudications", []) or []
            verdict_ids = {a.get("adjudication_id") for a in verdict_adj if isinstance(a, dict)}
            for exp in expected:
                if exp.get("adjudication_id") not in verdict_ids:
                    errors.append(
                        f"verdict.meta_review.adjudications missing canonical entry "
                        f"{exp.get('adjudication_id')} for propagated blocker "
                        f"({exp.get('persona')}, hash={exp.get('blocker_summary_hash')}); "
                        f"run-local binding required (AC-11 R2)"
                    )
        except (ImportError, ValueError, TypeError) as _e:
            print(f"validate_ensemble_output: WARN - adjudication binding check skipped: {_e}",
                  file=sys.stderr)

    if errors:
        print(f"validate_ensemble_output: FAIL - {len(errors)} error(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"validate_ensemble_output: PASS - {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
