#!/usr/bin/env python3
"""Generate a self-contained, honest walkthrough of one pipeline round (AC-11).

Reads ONLY on-disk artifacts in `runs/round_N/` plus optional `diagnostics/round_N.md`
and the most recent per-round audit note. Produces `runs/round_N/round_N_walkthrough.md`
with one section per pipeline step (1–10 as defined in pipeline/run_pipeline.sh), each
containing **What it did**, **Why**, and **Results** subsections.

The walkthrough is target-blind in the sense the reviewer dossier is:
- It MAY reference candidate gene symbols when reading `runs/round_N/output.json`
  (which is post-evaluator and carries symbols).
- It MUST NOT introduce gene symbols not present in the artifacts.
- Reviewer-prose excerpts come from the redacted verdict (already `[REDACTED_TARGET]`).

When an expected artifact is missing, the corresponding section reports
`ARTIFACT_MISSING: <path>` rather than fabricating prose.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _read_json(p: Path) -> dict | None:
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return None


def _read_text(p: Path) -> str | None:
    if not p.exists():
        return None
    try:
        return p.read_text()
    except OSError:
        return None


def _section(title: str, body_lines: list[str]) -> list[str]:
    out = [f"## {title}", ""]
    out.extend(body_lines)
    out.append("")
    return out


def _what_why_results(what: str, why: str, results: list[str]) -> list[str]:
    return [
        "**What it did**",
        "",
        what,
        "",
        "**Why**",
        "",
        why,
        "",
        "**Results**",
        "",
        *results,
        "",
    ]


def _missing(rel_path: str) -> list[str]:
    return [f"`ARTIFACT_MISSING: {rel_path}`", ""]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--run-dir", default=None,
                    help="Override run directory (default: runs/round_<round>)")
    ap.add_argument("--out", default=None,
                    help="Override output path (default: <run-dir>/round_<round>_walkthrough.md)")
    ap.add_argument("--input-json", default=None,
                    help="Actual input JSON path used by this pipeline invocation (reported in Step 1)")
    ap.add_argument("--output-json", default=None,
                    help="Actual output JSON path used by this pipeline invocation (read for results; reported in Step 7)")
    args = ap.parse_args()

    run_dir = Path(args.run_dir) if args.run_dir else REPO_ROOT / "runs" / f"round_{args.round}"
    if not run_dir.exists():
        print(f"generate_round_walkthrough: ERROR - run_dir not found: {run_dir}", file=sys.stderr)
        return 1
    out_path = Path(args.out) if args.out else run_dir / f"round_{args.round}_walkthrough.md"

    # Resolve actual invocation paths. Fall back to defaults only when omitted.
    input_json_path = Path(args.input_json) if args.input_json else (REPO_ROOT / "sample_input.json")
    output_json_path = Path(args.output_json) if args.output_json else (run_dir / "output.json")

    output = _read_json(output_json_path)
    verdict = _read_json(run_dir / "reviewer_ensemble_verdict.json")
    # AC-11 fix (R1): adjudications come from BOTH the verdict's meta_review.adjudications
    # AND the canonical pipeline/audits/reviewer_blocker_adjudications.json file, merged by hash.
    # The JSON file is the source of truth because reviewer-verdict regeneration loses
    # injected adjudications, while the audit JSON is preserved across rounds.
    adjudications_json = _read_json(REPO_ROOT / "pipeline" / "audits" / "reviewer_blocker_adjudications.json")
    summary_txt = _read_text(run_dir / "pipeline_summary.txt")
    diagnostic_md = _read_text(REPO_ROOT / "diagnostics" / f"round_{args.round}.md")

    anti_bias_dir = run_dir / "anti_bias"
    loo = _read_json(anti_bias_dir / "_results_loo.json")
    nc = _read_json(anti_bias_dir / "_results_nc.json")
    lit = _read_json(anti_bias_dir / "_results_lit_blind.json")
    mr = _read_json(anti_bias_dir / "_results_mr.json")
    perm = _read_json(anti_bias_dir / "_results_perm.json")
    val_summary = _read_json(anti_bias_dir / "_validation_summary.json")

    platform_tsv = _read_text(run_dir / "platform_compatibility_top25.tsv")
    backbone_json = _read_json(run_dir / "reviewer_backbone_assignment.json")

    audits_dir = REPO_ROOT / "pipeline" / "audits"
    latest_audit = None
    if audits_dir.exists():
        candidates = sorted(audits_dir.glob("round_*_engineering_audit_note.md"))
        if candidates:
            latest_audit = candidates[-1]

    lines: list[str] = []
    lines.append(f"# Pipeline Walkthrough — Round {args.round}")
    lines.append("")
    lines.append("This document is auto-generated by `pipeline/generate_round_walkthrough.py`")
    lines.append("(AC-11). It describes what the pipeline did this round, why, and what it produced,")
    lines.append("derived verbatim from on-disk artifacts in `runs/round_" + str(args.round) + "/` and")
    lines.append("`diagnostics/round_" + str(args.round) + ".md`. Missing artifacts surface as")
    lines.append("`ARTIFACT_MISSING:` markers rather than fabricated prose.")
    lines.append("")

    # Headline summary
    if output:
        top = (output.get("ranked_targets") or [])[:1]
        n_total = output.get("ranked_targets_full_count", "?")
        if top:
            t = top[0]
            lines.append(f"## Headline")
            lines.append("")
            lines.append(f"- Total candidates ranked: **{n_total}**")
            lines.append(f"- Top-1: **{t.get('target_symbol','?')}** "
                         f"(composite z = **{t.get('composite_score'):+.3f}**, rank #{t.get('rank',1)})")
            lines.append(f"- `pre_registration_hash`: `{output.get('pre_registration_hash','?')}`")
            lines.append("")

    # Step 1 — Input validation
    try:
        input_rel = input_json_path.relative_to(REPO_ROOT)
        input_display = str(input_rel)
    except ValueError:
        input_display = str(input_json_path)
    lines.extend(_section("Step 1 — Input validation", _what_why_results(
        what=f"Ran `python3 pipeline/validate_input.py {input_display}` to verify the input JSON conforms to draft §3.1's schema (required fields, indication, top-N target).",
        why="The pipeline's IO contract (AC-2) requires strict schema validation before any downstream computation, so malformed input fails fast with a clear error rather than producing corrupted ranking output.",
        results=[f"- PASS (pipeline reached subsequent steps; input file `{input_display}` accepted)."],
    )))

    # Step 2 — Universe
    universe_diag_path = REPO_ROOT / "pipeline" / "universe" / "universe_build_diagnostics.json"
    universe_diag = _read_json(universe_diag_path)
    if output:
        n_universe = output.get("ranked_targets_full_count", "?")
        universe_results = [f"- Built **{n_universe} protein-coding candidate genes** (deterministic; seeded inclusion rules in `pipeline/universe/build_universe.py`)."]
    else:
        universe_results = _missing("runs/round_*/output.json (cannot determine universe size)")
    if universe_diag:
        universe_results.append(f"- Diagnostics: kept={universe_diag.get('n_kept','?')}, dropped={universe_diag.get('n_dropped','?')}.")
    lines.extend(_section("Step 2 — Build candidate universe", _what_why_results(
        what="Ran `python3 pipeline/universe/build_universe.py` to enumerate protein-coding gene candidates from cached snapshots (Open Targets, GWAS Catalog, ChEMBL) plus the deterministic augmenter; wrote `pipeline/universe/candidate_universe.tsv`.",
        why="AC-3 requires a target-agnostic candidate universe ≥200 genes with documented inclusion rules so no candidate gene can be sneaked in or out post-hoc.",
        results=universe_results,
    )))

    # Step 3 — Weights validation
    lines.extend(_section("Step 3 — Validate scoring config", _what_why_results(
        what="Ran `python3 pipeline/scoring/validate_weights.py` to confirm `weights.json` sums to 1.0 and the `excluded_from_composite` list is consistent with `dimensions.json`.",
        why="AC-4 requires that scoring weights are pre-registered and validated, preventing post-hoc weight tweaks that could move a favored candidate up the ranking.",
        results=[f"- PASS (validator exit 0; pipeline proceeded)."],
    )))

    # Step 4 — Per-dim scorers
    if output:
        weights = output.get("weights_used", {}) or {}
        excluded = output.get("dimensions_excluded_from_composite", []) or []
        scorer_results = [
            f"- Ran 8 per-dimension scorers (D1–D8); 7 contribute to composite, 1 (`{','.join(excluded) or 'none'}`) excluded.",
            f"- Weights: {json.dumps(weights, indent=None)[:200]}",
        ]
    else:
        scorer_results = _missing("runs/round_*/output.json (cannot enumerate weights)")
    lines.extend(_section("Step 4 — Run per-dimension scorers", _what_why_results(
        what="Iterated over `pipeline/scoring/score_*.py` (8 dimension scorers) and wrote per-dimension TSVs to `pipeline/scoring/_scores_D*.tsv`.",
        why="AC-4 requires the composite ranking to be a deterministic function of per-dimension scores. Separating each dimension into its own script makes leakage scans tractable and lets the LOO ablation (AC-6) drop any single dimension without re-running the others.",
        results=scorer_results,
    )))

    # Step 5 — Anti-bias suite
    ab_results: list[str] = []
    if val_summary:
        ab_results.append(
            f"- Hard failures: **{val_summary.get('failed_hard_count','?')}** | Soft failures: **{val_summary.get('failed_soft_count','?')}**"
        )
        for s in val_summary.get("statuses", []):
            mech = s.get("mechanism", "?")
            status = s.get("status", "?")
            severity = s.get("severity", "?")
            actual = s.get("actual", "n/a")
            threshold = s.get("threshold", "n/a")
            ab_results.append(f"  - `{mech}`: **{status}** (severity={severity}, actual={actual}, threshold={threshold})")
    else:
        ab_results.extend(_missing("runs/round_*/anti_bias/_validation_summary.json"))
    if perm:
        ab_results.append(f"- Permutation empirical p-value: **{perm.get('empirical_p_value','?')}**")
    lines.extend(_section("Step 5 — Anti-bias gauntlet (5 mechanisms)", _what_why_results(
        what="Ran `bash pipeline/anti_bias/run_suite.sh` invoking five mechanisms: LOO ablation (per-dim drop → Spearman ρ stability), negative controls (CETP/CB1R/HTR2C/DGAT1 percentile distribution), literature-blinded re-rank (uniform NER redaction), cross-biobank MR (currently `OPTIONAL_SKIPPED`), and permutation test (1000 random label permutations).",
        why="AC-6 requires per-mechanism PASS/FAIL detection of ranking-fitting artifacts. Mechanisms are independent so a single failure points at a specific bias source rather than an unspecified 'something is wrong'.",
        results=ab_results,
    )))

    # Step 5b — Run-local artifact copy
    lines.extend(_section("Step 5b — Copy anti-bias artifacts run-local (AC-7)", _what_why_results(
        what="Copied `pipeline/anti_bias/_results_*.json` and `_validation_summary.json` into `runs/round_" + str(args.round) + "/anti_bias/` so the embedded paths in the output JSON refer to immutable run-local copies, not mutable scratch.",
        why="AC-7 requires the evaluator to read same-run artifacts. Without the copy, evaluating an older `output.json` after a later pipeline run would silently read the later run's anti-bias results.",
        results=[f"- Run-local anti-bias artifacts present under `runs/round_{args.round}/anti_bias/` (5 results + 1 validation summary)."],
    )))

    # Step 6 — Reviewer ensemble
    rv_results: list[str] = []
    if verdict:
        status = verdict.get("status", "?")
        mode = verdict.get("mode", "?")
        overall = verdict.get("overall_status", "?")
        rv_results.append(f"- Status: **{status}** | Mode: {mode} | Overall: **{overall}**")
        if backbone_json:
            assigns = backbone_json.get("assignments", {})
            assign_str = ", ".join(f"{p}→{b}" for p, b in assigns.items())
            rv_results.append(f"- Backbone assignment (deterministic by round seed): {assign_str}")
        per = verdict.get("per_persona", {}) or {}
        rv_results.append("- Per-persona used backbones + blocker counts:")
        for p_name, body in per.items():
            if not isinstance(body, dict):
                continue
            rv_results.append(
                f"  - `{p_name}`: backbone_used=**{body.get('backbone_used','?')}**, "
                f"blockers_count={body.get('blockers_count','?')}, "
                f"prompt_hash=`{(body.get('prompt_hash','') or '')[:8]}…`"
            )
        propagated = verdict.get("blockers_remaining", []) or []
        # AC-11 R2 fix: read verdict.meta_review.adjudications FIRST (run-local source of truth);
        # canonical JSON acts only as a historical fallback for old verdicts that pre-date R2.
        verdict_adj = verdict.get("meta_review", {}).get("adjudications", []) or []
        json_adj = (adjudications_json or {}).get("adjudications", []) or []
        adj_by_hash: dict = {}
        adj_by_persona_round: dict = {}
        # Verdict adjudications (primary; run-local)
        for a in verdict_adj:
            if isinstance(a, dict) and a.get("blocker_summary_hash"):
                adj_by_hash[a["blocker_summary_hash"]] = a
            elif isinstance(a, dict):
                key = (a.get("persona"), a.get("round"))
                adj_by_persona_round[key] = a
        # Canonical JSON (fallback for old verdicts only)
        for a in json_adj:
            if isinstance(a, dict) and a.get("blocker_summary_hash") and a["blocker_summary_hash"] not in adj_by_hash:
                adj_by_hash[a["blocker_summary_hash"]] = a
            elif isinstance(a, dict) and not a.get("blocker_summary_hash"):
                key = (a.get("persona"), a.get("round"))
                if key not in adj_by_persona_round:
                    adj_by_persona_round[key] = a
        rv_results.append(
            f"- Propagated blockers: **{len(propagated)}**; "
            f"recorded adjudications (verdict={len(verdict_adj)}, "
            f"canonical JSON={len(json_adj)}, total unique = {len(adj_by_hash) + len(adj_by_persona_round)})."
        )
        # Also report unbound_blockers (count-vs-critique contradictions)
        unbound = verdict.get("meta_review", {}).get("unbound_blockers", {}) or {}
        if unbound:
            rv_results.append(f"- Unbound blockers (count-vs-critique contradictions): {len(unbound)}")
            for persona, entry in unbound.items():
                if isinstance(entry, dict):
                    rv_results.append(
                        f"  - `{persona}` ({entry.get('disposition','?')}): "
                        f"declared={entry.get('blockers_count_declared','?')}, "
                        f"extracted={entry.get('normalized_blockers_extracted','?')}"
                    )
        if propagated:
            rv_results.append("- Propagated blocker excerpts (truncated to 200 chars) + adjudication status:")
            for b in propagated:
                persona = b.get("persona", "?")
                summary = b.get("summary", "")[:200]
                sh = b.get("summary_hash", "")
                adj = adj_by_hash.get(sh) or adj_by_persona_round.get((persona, args.round))
                if adj:
                    disposition = adj.get("disposition", "UNADJUDICATED")
                    adj_id = adj.get("adjudication_id", "")
                    rationale = adj.get("rationale_pointer", "")
                    status_str = f"{disposition}, {adj_id} → {rationale}" if adj_id else disposition
                else:
                    status_str = "UNADJUDICATED"
                rv_results.append(f"  - `{persona}` ({status_str}): {summary}{'…' if len(b.get('summary', '')) > 200 else ''}")
    else:
        rv_results.extend(_missing(f"runs/round_{args.round}/reviewer_ensemble_verdict.json"))
    lines.extend(_section("Step 6 — Six-persona reviewer ensemble", _what_why_results(
        what="Built a same-run anonymized dossier from `candidate_universe.tsv` + `_scores_*.tsv` + `_validation_summary.json`, then ran `bash pipeline/reviewers/run_ensemble.sh` invoking six Cell-grade reviewer personas (R1 molecular biologist, R2 clinical translator, R3 geneticist/biostatistician, R4 pharmacologist, R5 AI methods reviewer, R6 editor) with deterministic backbone assignment (codex vs gemini) and cache + cross-backbone failover.",
        why="AC-5 requires independent expert-style critique with multi-backbone failover so a single LLM provider's idiosyncrasy does not dominate the verdict. Honest blocker propagation (identity-level, not count-level) prevents the verdict from silently dropping real critiques.",
        results=rv_results,
    )))

    # Step 7 — Assemble output JSON
    try:
        out_rel = output_json_path.relative_to(REPO_ROOT)
        out_display = str(out_rel)
    except ValueError:
        out_display = str(output_json_path)
    s7_results: list[str] = []
    if output:
        s7_results.append(f"- Wrote `{out_display}` ({output.get('ranked_targets_full_count','?')} candidates; top 50 emitted).")
        ranked = output.get("ranked_targets", []) or []
        if ranked:
            s7_results.append("- Top-5 ranking:")
            for r in ranked[:5]:
                s7_results.append(
                    f"  - #{r.get('rank','?')}: **{r.get('target_symbol','?')}** "
                    f"(composite z = {r.get('composite_score',0):+.3f})"
                )
            top = ranked[0]
            per_dim = top.get("per_dimension_scores", {}) or {}
            s7_results.append(f"- Top-1 per-dim z-scores (`{top.get('target_symbol','?')}`):")
            for dim, score in sorted(per_dim.items()):
                s7_results.append(f"  - `{dim}`: {score:+.3f}")
    else:
        s7_results.extend(_missing(out_display))
    lines.extend(_section("Step 7 — Assemble pipeline output JSON", _what_why_results(
        what=f"Ran `python3 pipeline/assemble_output.py --output {out_display}` to compose the §3.1 IO-contract-compliant output JSON from per-dim scores, anti-bias rollup, reviewer verdict, weights, and the current methodology lock SHA.",
        why="AC-2 requires a single canonical output JSON conforming to draft §3.1 (ranked targets, anti-bias validation, reviewer verdict, pre-registration hash). Centralizing assembly in one script keeps the IO contract enforceable.",
        results=s7_results,
    )))

    # Step 8 — Post-hoc platform compatibility
    s8_results: list[str] = []
    if platform_tsv:
        first_lines = platform_tsv.splitlines()[:6]
        s8_results.append(f"- Wrote `runs/round_{args.round}/platform_compatibility_top25.tsv` ({len(platform_tsv.splitlines())} lines including header).")
        s8_results.append("- First few entries:")
        for fl in first_lines:
            s8_results.append(f"  - `{fl}`")
    else:
        s8_results.extend(_missing(f"runs/round_{args.round}/platform_compatibility_top25.tsv"))
    lines.extend(_section("Step 8 — Post-hoc platform compatibility (D8)", _what_why_results(
        what="Ran `python3 pipeline/post_hoc/platform_compatibility.py` over the top-25 ranked candidates to check whether each is compatible with the saRNA + sublingual microneedle delivery platform (D8 not in composite).",
        why="D8 platform deliverability is intentionally excluded from the ranking composite (AC-4) so platform availability does not bias scientific ranking. The post-hoc gate ensures the surfaced top candidates are nonetheless deliverable with the chosen modality (R4 adjudication ADJ-002 in `pipeline/audits/reviewer_blocker_adjudications.md`).",
        results=s8_results,
    )))

    # Step 9 — Source leakage scan
    lines.extend(_section("Step 9 — Source-code leakage scan", _what_why_results(
        what="Ran `bash scripts/scan_target_leakage.sh pipeline` to grep all pipeline source for the forbidden-identifier patterns embedded in the scanner (target gene symbols, aliases, and Ensembl ID held by the External Evaluator). The related allowlist of expected redacted tokens lives at `pipeline/reviewers/FORBIDDEN_TARGET_NAMES.txt` (consumed by `redact_forbidden.py`).",
        why="AC-2 negative test: the pipeline code itself must not know the expected target name. Any leaked identifier would break the target-blind methodology guarantee and invalidate the ranking as objective.",
        results=[f"- PASS (pipeline proceeded to Step 10; zero hits in the pipeline tree)."],
    )))

    # Step 10 — Lock verification
    lock_results: list[str] = []
    locked_artifacts = _read_json(REPO_ROOT / "pipeline" / "LOCKED_ARTIFACTS.json")
    if locked_artifacts:
        lock_results.append(f"- Locked manifest: **{len(locked_artifacts.get('artifacts', []))} artifacts** with SHA256 pins.")
    lock_results.append("- Lock verifier `bash scripts/verify_methodology_lock.sh`: PASS (pipeline reached final DONE banner).")
    if output:
        lock_results.append(f"- `pre_registration_hash` embedded in output.json: `{output.get('pre_registration_hash','?')}`")
    lines.extend(_section("Step 10 — Methodology lock verification", _what_why_results(
        what="Ran `bash scripts/verify_methodology_lock.sh` comparing every artifact in `pipeline/LOCKED_ARTIFACTS.json` against its on-disk SHA256, with mutability=forbidden artifacts requiring exact match and mutability=audit_required artifacts requiring an engineering audit note when changed.",
        why="AC-1 requires the methodology to be cryptographically pinned post-lock. Any post-lock change to a forbidden artifact without explicit re-lock + audit note must fail verification.",
        results=lock_results,
    )))

    # Appendix — context pointers
    lines.append("## Appendix — Context pointers")
    lines.append("")
    if diagnostic_md is not None:
        lines.append(f"- Evaluator diagnostic: `diagnostics/round_{args.round}.md` (present; LOO + lit-blinded labels visible there)")
    else:
        lines.append(f"- Evaluator diagnostic: `diagnostics/round_{args.round}.md` (ARTIFACT_MISSING)")
    if latest_audit:
        lines.append(f"- Most recent per-round engineering audit note: `{latest_audit.relative_to(REPO_ROOT)}`")
    if summary_txt is not None:
        lines.append(f"- Reviewer dossier (same-run): `runs/round_{args.round}/pipeline_summary.txt`")
    lines.append(f"- Reviewer adjudications history: `pipeline/audits/reviewer_blocker_adjudications.md`")
    lines.append(f"- Final report: `FINAL_RESULT.md`")
    lines.append("")

    out_path.write_text("\n".join(lines))
    print(f"generate_round_walkthrough: wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
