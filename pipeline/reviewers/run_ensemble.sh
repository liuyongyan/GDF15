#!/usr/bin/env bash
# run_ensemble.sh - Invoke the six-persona reviewer ensemble.
#
# Usage: run_ensemble.sh <round_number> <input_summary_path> <output_dir>
#
# Performs randomized backbone assignment per persona, invokes each persona's
# critique via the assigned LLM CLI, and aggregates into reviewer_ensemble_verdict.json.
#
# For Round 0, this script uses MOCK responses (deterministic stubs) so the
# end-to-end pipeline is runnable without consuming LLM quota. Real LLM invocations
# are added in subsequent rounds once the calling code is verified end-to-end.

set -euo pipefail

ROUND_NUMBER="${1:-0}"
INPUT_SUMMARY="${2:-}"
OUTPUT_DIR="${3:-runs/round_$ROUND_NUMBER}"

if [[ -z "$INPUT_SUMMARY" ]] || [[ ! -f "$INPUT_SUMMARY" ]]; then
    echo "run_ensemble: ERROR - input summary not found: $INPUT_SUMMARY" >&2
    exit 2
fi

mkdir -p "$OUTPUT_DIR"

# Randomized backbone assignment per persona, deterministic by round
PERSONAS=(R1_molecular_biologist R2_clinical_translator R3_geneticist_biostatistician R4_pharmacologist R5_ai_methods_reviewer R6_editor)

ASSIGNMENT_JSON="$OUTPUT_DIR/reviewer_backbone_assignment.json"
echo "{" > "$ASSIGNMENT_JSON"
echo "  \"round\": $ROUND_NUMBER," >> "$ASSIGNMENT_JSON"
echo "  \"seed\": $ROUND_NUMBER," >> "$ASSIGNMENT_JSON"
echo "  \"assignment_method\": \"deterministic_pseudorandom_by_round\"," >> "$ASSIGNMENT_JSON"
echo "  \"assignments\": {" >> "$ASSIGNMENT_JSON"

last=$((${#PERSONAS[@]} - 1))
for i in "${!PERSONAS[@]}"; do
    persona="${PERSONAS[$i]}"
    # Deterministic pseudo-random: hash of (round_number, persona_index)
    hash_val=$(printf "%s_%s" "$ROUND_NUMBER" "$i" | shasum | awk '{print $1}' | head -c 4)
    n=$((16#$hash_val % 2))
    if [[ $n -eq 0 ]]; then backbone="codex"; else backbone="gemini"; fi
    sep=""
    if [[ $i -ne $last ]]; then sep=","; fi
    echo "    \"$persona\": \"$backbone\"$sep" >> "$ASSIGNMENT_JSON"
done

echo "  }" >> "$ASSIGNMENT_JSON"
echo "}" >> "$ASSIGNMENT_JSON"

echo "run_ensemble: backbone assignment written to $ASSIGNMENT_JSON"

# For Round 0, generate MOCK reviewer outputs (deterministic stubs).
# Subsequent rounds will replace these with real LLM invocations.
OUTPUT_VERDICT="$OUTPUT_DIR/reviewer_ensemble_verdict.json"
cat > "$OUTPUT_VERDICT" <<EOF
{
  "schema_version": "1.0",
  "round": $ROUND_NUMBER,
  "mode": "MOCK_STUB_FOR_ROUND_0",
  "note": "Round 0 emits deterministic stubs to verify end-to-end plumbing. Real LLM invocation replaces this stub in Round 1+.",
  "per_persona": {
    "R1_molecular_biologist": {
      "persona": "R1_molecular_biologist",
      "critiques": [],
      "global_methodology_notes": ["Round 0 mock — pending real review"],
      "blockers_count": 0
    },
    "R2_clinical_translator": {
      "persona": "R2_clinical_translator",
      "critiques": [],
      "global_methodology_notes": ["Round 0 mock — pending real review"],
      "blockers_count": 0
    },
    "R3_geneticist_biostatistician": {
      "persona": "R3_geneticist_biostatistician",
      "critiques": [],
      "pipeline_methodology_critique": "Round 0 mock — pending real review",
      "global_methodology_notes": [],
      "blockers_count": 0
    },
    "R4_pharmacologist": {
      "persona": "R4_pharmacologist",
      "critiques": [],
      "global_methodology_notes": ["Round 0 mock — pending real review"],
      "blockers_count": 0
    },
    "R5_ai_methods_reviewer": {
      "persona": "R5_ai_methods_reviewer",
      "critiques": [],
      "pipeline_methodology_critique": "Round 0 mock — pending real review",
      "global_methodology_notes": [],
      "blockers_count": 0
    },
    "R6_editor": {
      "persona": "R6_editor",
      "pipeline_methodology_critique": "Round 0 mock — pending real review",
      "cell_fit_recommendation": "deferred_for_round_0_stub",
      "global_methodology_notes": [],
      "blockers_count": 0
    }
  },
  "meta_review": {
    "verdict": "deferred_for_round_0_stub",
    "consensus_blockers": [],
    "single_reviewer_blockers": [],
    "pipeline_methodology_concerns": ["Real LLM critique pending Round 1+"],
    "cross_reviewer_agreement_summary": "Round 0 stub — no agreement matrix yet"
  },
  "blockers_remaining": []
}
EOF

echo "run_ensemble: wrote $OUTPUT_VERDICT (MOCK STUB for Round 0)"
exit 0
