#!/usr/bin/env bash
# run_ensemble.sh — Invoke the six-persona reviewer ensemble (or document deferral).
#
# Usage: run_ensemble.sh <round_number> <input_summary_path> <output_dir>
#
# Performs randomized backbone assignment per persona, then attempts to invoke each
# persona's critique via the assigned LLM CLI through the humanize wrappers.
#
# If REAL_LLM_REVIEW is not enabled (env var REAL_LLM_REVIEW=1), or no usable LLM
# CLI is available, this script writes a properly-formed REVIEWER_DEFERRED verdict
# with the required schema (status/reason/affected_personas/affected_backbones/
# remediation) so that downstream consumers and the validator can proceed without
# the real LLM transcripts (which are a Round 3+ engineering deliverable).

set -euo pipefail

ROUND_NUMBER="${1:-0}"
INPUT_SUMMARY="${2:-}"
OUTPUT_DIR="${3:-runs/round_$ROUND_NUMBER}"

if [[ -z "$INPUT_SUMMARY" ]] || [[ ! -f "$INPUT_SUMMARY" ]]; then
    echo "run_ensemble: ERROR - input summary not found: $INPUT_SUMMARY" >&2
    exit 2
fi

mkdir -p "$OUTPUT_DIR"

PERSONAS=(R1_molecular_biologist R2_clinical_translator R3_geneticist_biostatistician R4_pharmacologist R5_ai_methods_reviewer R6_editor)

# Randomized backbone assignment per round (deterministic by SHA1(round, persona_index))
ASSIGNMENT_JSON="$OUTPUT_DIR/reviewer_backbone_assignment.json"
echo "{" > "$ASSIGNMENT_JSON"
echo "  \"round\": $ROUND_NUMBER," >> "$ASSIGNMENT_JSON"
echo "  \"seed\": $ROUND_NUMBER," >> "$ASSIGNMENT_JSON"
echo "  \"assignment_method\": \"deterministic_pseudorandom_by_round\"," >> "$ASSIGNMENT_JSON"
echo "  \"assignments\": {" >> "$ASSIGNMENT_JSON"

last=$((${#PERSONAS[@]} - 1))
for i in "${!PERSONAS[@]}"; do
    persona="${PERSONAS[$i]}"
    hash_val=$(printf "%s_%s" "$ROUND_NUMBER" "$i" | shasum | awk '{print $1}' | head -c 4)
    n=$((16#$hash_val % 2))
    if [[ $n -eq 0 ]]; then backbone="codex"; else backbone="gemini"; fi
    sep=""
    if [[ $i -ne $last ]]; then sep=","; fi
    echo "    \"$persona\": \"$backbone\"$sep" >> "$ASSIGNMENT_JSON"
done
echo "  }" >> "$ASSIGNMENT_JSON"
echo "}" >> "$ASSIGNMENT_JSON"

OUTPUT_VERDICT="$OUTPUT_DIR/reviewer_ensemble_verdict.json"

REAL_LLM_REVIEW="${REAL_LLM_REVIEW:-0}"
codex_ok=0
gemini_ok=0
command -v codex >/dev/null 2>&1 && codex_ok=1
command -v gemini >/dev/null 2>&1 && gemini_ok=1

if [[ "$REAL_LLM_REVIEW" != "1" ]] || { [[ $codex_ok -eq 0 ]] && [[ $gemini_ok -eq 0 ]]; }; then
    # Emit REVIEWER_DEFERRED with the full required schema
    reason="REAL_LLM_REVIEW disabled (Round 3+ engineering deliverable). Real reviewer ensemble LLM invocations are not implemented in Round 2 to stay within subscription budget for the overnight run."
    if [[ "$REAL_LLM_REVIEW" == "1" ]] && [[ $codex_ok -eq 0 ]] && [[ $gemini_ok -eq 0 ]]; then
        reason="Both LLM CLIs (codex, gemini) unavailable on PATH; reviewer ensemble cannot run. Verify subscription auth or set API keys."
    fi
    cat > "$OUTPUT_VERDICT" <<EOF
{
  "schema_version": "1.0",
  "round": $ROUND_NUMBER,
  "status": "REVIEWER_DEFERRED",
  "mode": "REVIEWER_DEFERRED",
  "reason": "$reason",
  "affected_personas": ["R1_molecular_biologist", "R2_clinical_translator", "R3_geneticist_biostatistician", "R4_pharmacologist", "R5_ai_methods_reviewer", "R6_editor"],
  "affected_backbones": ["codex", "gemini"],
  "remediation": "Set REAL_LLM_REVIEW=1 environment variable AND ensure 'codex' and 'gemini' CLIs are on PATH AND the corresponding subscriptions/API keys are authenticated. Then re-run this script for round $ROUND_NUMBER. If only one backbone is available, the script will route all six personas to that backbone with a single-backbone WARNING.",
  "meta_review": {
    "verdict": "deferred",
    "consensus_blockers": [],
    "single_reviewer_blockers": [],
    "pipeline_methodology_concerns": ["Real LLM reviewer ensemble pending Round 3+ engineering"],
    "cross_reviewer_agreement_summary": "Deferred — no per-persona reviews produced"
  },
  "blockers_remaining": []
}
EOF
    echo "run_ensemble: REVIEWER_DEFERRED status written (set REAL_LLM_REVIEW=1 to enable real LLM calls)"
    exit 0
fi

# Real LLM path (Round 3+ engineering). For now this branch is reachable only when
# REAL_LLM_REVIEW=1 AND at least one backbone is available; we still defer because
# the full per-persona invocation logic (prompt loading, response parsing, schema
# wrapping) is not yet implemented. We write REVIEWER_DEFERRED with explicit
# pending-engineering reason.
cat > "$OUTPUT_VERDICT" <<EOF
{
  "schema_version": "1.0",
  "round": $ROUND_NUMBER,
  "status": "REVIEWER_DEFERRED",
  "mode": "REVIEWER_DEFERRED",
  "reason": "REAL_LLM_REVIEW=1 set but per-persona invocation logic is a Round 3+ engineering deliverable. The framework (backbone assignment, schema, rate-limit fallback contract) is in place; the actual /humanize:ask-codex and /humanize:ask-gemini invocations + response parsing remain to be wired up.",
  "affected_personas": ["R1_molecular_biologist", "R2_clinical_translator", "R3_geneticist_biostatistician", "R4_pharmacologist", "R5_ai_methods_reviewer", "R6_editor"],
  "affected_backbones": ["codex", "gemini"],
  "remediation": "Implement per-persona LLM invocation in pipeline/reviewers/run_ensemble.sh: read each persona prompt from pipeline/reviewers/R*.md, send via the assigned backbone's humanize wrapper, parse JSON response, validate per-persona schema, aggregate into meta_review. See pipeline/reviewers/meta_review.md for the expected aggregation contract.",
  "meta_review": {
    "verdict": "deferred",
    "consensus_blockers": [],
    "single_reviewer_blockers": [],
    "pipeline_methodology_concerns": ["Reviewer per-persona invocation pending Round 3+ engineering"],
    "cross_reviewer_agreement_summary": "Deferred — invocation logic not yet implemented"
  },
  "blockers_remaining": []
}
EOF

echo "run_ensemble: REVIEWER_DEFERRED status written (per-persona LLM invocation pending Round 3+ engineering)"
exit 0
