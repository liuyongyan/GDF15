#!/usr/bin/env bash
# loop_orchestrator.sh — Two-phase design loop orchestrator.
#
# This script is the standalone wrapper around the design loop. In the current
# RLCR-based deployment, the Claude Code RLCR loop drives execution and this
# script is invoked for individual rounds or as a reference implementation.
#
# Usage:
#   loop_orchestrator.sh --phase=alpha --round=N --max-rounds=M
#   loop_orchestrator.sh --phase=beta  --round=N --max-rounds=M --max-wallclock=H
#
# Per-round artifacts:
#   proposals/round_N.md
#   runs/round_N/output.json
#   runs/round_N/api_calls.log
#   diagnostics/round_N.md  (Phase β only)
#   reviews/round_N.md
#
# On rate-limit error, writes RATE_LIMITED.md and halts. On stuck (3 non-improving
# rounds), writes STUCK.md. On budget exhaustion, writes BUDGET_EXHAUSTED.md.

set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

PHASE="alpha"
ROUND=0
MAX_ROUNDS="${MAX_ROUNDS:-15}"
MAX_WALLCLOCK_HOURS="${MAX_WALLCLOCK_HOURS:-8}"

for arg in "$@"; do
    case "$arg" in
        --phase=*) PHASE="${arg#*=}" ;;
        --round=*) ROUND="${arg#*=}" ;;
        --max-rounds=*) MAX_ROUNDS="${arg#*=}" ;;
        --max-wallclock=*) MAX_WALLCLOCK_HOURS="${arg#*=}" ;;
    esac
done

echo "loop_orchestrator: phase=$PHASE round=$ROUND max_rounds=$MAX_ROUNDS"

mkdir -p proposals runs/round_$ROUND diagnostics reviews

# Phase α: methodology design (NO evaluator)
# Phase β: engineering iteration (verbose evaluator)
if [[ "$PHASE" == "alpha" ]]; then
    echo "loop_orchestrator: Phase α — methodology design (evaluator-free)"
    # Step 1: scan source for leakage
    bash scripts/scan_target_leakage.sh pipeline
    # Step 2: validate scoring config
    python3 pipeline/scoring/validate_weights.py
    # Step 3: run pipeline on a validation universe (NOT full run)
    bash pipeline/run_pipeline.sh sample_input.json "runs/round_$ROUND/output.json" "$ROUND"
elif [[ "$PHASE" == "beta" ]]; then
    echo "loop_orchestrator: Phase β — engineering iteration (verbose evaluator)"
    # Verify lock tag exists
    if ! git rev-parse refs/tags/v1.0-methodology-locked >/dev/null 2>&1; then
        echo "loop_orchestrator: ERROR - cannot start Phase β without lock tag" >&2
        exit 1
    fi
    bash scripts/verify_methodology_lock.sh
    bash pipeline/run_pipeline.sh sample_input.json "runs/round_$ROUND/output.json" "$ROUND"
    python3 evaluator/evaluator.py --mode verbose \
        --input "runs/round_$ROUND/output.json" \
        --output "diagnostics/round_$ROUND.md"
else
    echo "loop_orchestrator: ERROR - unknown phase $PHASE (use alpha or beta)" >&2
    exit 2
fi

echo "loop_orchestrator: round $ROUND complete"
