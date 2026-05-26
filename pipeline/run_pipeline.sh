#!/usr/bin/env bash
# run_pipeline.sh — End-to-end Pipeline orchestrator.
#
# Usage: run_pipeline.sh <input_json> <output_json> [<round_number>]
#
# Performs the full sequence: universe build → per-dim scoring → reviewer ensemble →
# anti-bias suite → assemble output JSON → post-hoc platform compatibility check.

set -euo pipefail

INPUT_JSON="${1:-sample_input.json}"
OUTPUT_JSON="${2:-runs/round_0/output.json}"
ROUND_NUMBER="${3:-0}"

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$DIR")"
RUN_DIR="$ROOT/runs/round_$ROUND_NUMBER"

mkdir -p "$RUN_DIR"

echo "[run_pipeline] === Step 1: Validate input ==="
if [[ ! -f "$INPUT_JSON" ]]; then
    echo "[run_pipeline] WARNING: input $INPUT_JSON not found; using default research question"
fi

echo ""
echo "[run_pipeline] === Step 2: Build candidate universe ==="
python3 "$DIR/universe/build_universe.py"

echo ""
echo "[run_pipeline] === Step 3: Validate scoring config ==="
python3 "$DIR/scoring/validate_weights.py"

echo ""
echo "[run_pipeline] === Step 4: Run per-dimension scorers ==="
for s in "$DIR/scoring"/score_*.py; do
    python3 "$s"
done

echo ""
echo "[run_pipeline] === Step 5: Run anti-bias suite ==="
bash "$DIR/anti_bias/run_suite.sh"

echo ""
echo "[run_pipeline] === Step 6: Run reviewer ensemble ==="
SUMMARY_TXT="$RUN_DIR/pipeline_summary.txt"
echo "Pipeline summary input for reviewer ensemble (round $ROUND_NUMBER)" > "$SUMMARY_TXT"
bash "$DIR/reviewers/run_ensemble.sh" "$ROUND_NUMBER" "$SUMMARY_TXT" "$RUN_DIR"
python3 "$DIR/reviewers/validate_ensemble_output.py" "$RUN_DIR/reviewer_ensemble_verdict.json"
python3 "$DIR/reviewers/scan_reviewer_outputs.py" "$RUN_DIR/reviewer_ensemble_verdict.json" --phase=alpha

echo ""
echo "[run_pipeline] === Step 7: Assemble pipeline output JSON ==="
python3 "$DIR/assemble_output.py" \
    --reviewer-verdict "$RUN_DIR/reviewer_ensemble_verdict.json" \
    --output "$OUTPUT_JSON" \
    --round "$ROUND_NUMBER"

echo ""
echo "[run_pipeline] === Step 8: Post-hoc platform compatibility check ==="
python3 "$DIR/post_hoc/platform_compatibility.py" \
    "$OUTPUT_JSON" \
    "$RUN_DIR/platform_compatibility_top25.tsv"

echo ""
echo "[run_pipeline] === Step 9: Source leakage scan ==="
bash "$ROOT/scripts/scan_target_leakage.sh" "$DIR"

echo ""
echo "[run_pipeline] === Step 10: Methodology lock verification ==="
bash "$ROOT/scripts/verify_methodology_lock.sh"

echo ""
echo "[run_pipeline] === DONE ==="
echo "[run_pipeline] Output JSON:        $OUTPUT_JSON"
echo "[run_pipeline] Run directory:      $RUN_DIR"
echo "[run_pipeline] Top-25 platform:    $RUN_DIR/platform_compatibility_top25.tsv"
exit 0
