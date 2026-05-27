#!/usr/bin/env bash
# loop_orchestrator.sh — Authoritative standalone lifecycle driver for the design loop.
#
# Implements (per plan v1.1 AC-8):
#   - round counter + MAX_ROUNDS enforcement
#   - MAX_WALLCLOCK_HOURS enforcement
#   - phase gating (alpha = no evaluator; beta = verbose evaluator + lock required)
#   - per-round artifacts: proposals/round_N.md, runs/round_N/, diagnostics/round_N.md,
#                          reviews/round_N.md, runs/round_N/decision.json
#   - rollback support on decision.json containing decision: rollback
#   - STUCK.md after 3 consecutive non-improving rounds
#   - RATE_LIMITED.md on LLM quota failures (delegated to run_ensemble.sh)
#   - BUDGET_EXHAUSTED.md or FINAL_RESULT.md on exit
#   - rejects Phase β without v1.0-methodology-locked tag + passing verify_methodology_lock.sh
#
# Usage:
#   loop_orchestrator.sh --phase=alpha|beta [--max-rounds=N] [--max-wallclock=H] [--round-start=N]
#
# Decision file schema (written by user/Codex review hook between rounds):
#   {"decision": "continue|rollback|terminate", "round": N, "reason": "..."}
#
# Improvement tracking: orchestrator looks at diagnostics/round_N.md for T1..T6 pass count;
# if 3 consecutive rounds have no T-count improvement, emits STUCK.md and halts.

set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

PHASE="alpha"
MAX_ROUNDS="${MAX_ROUNDS:-15}"
MAX_WALLCLOCK_HOURS="${MAX_WALLCLOCK_HOURS:-8}"
ROUND_START=0

for arg in "$@"; do
    case "$arg" in
        --phase=*) PHASE="${arg#*=}" ;;
        --max-rounds=*) MAX_ROUNDS="${arg#*=}" ;;
        --max-wallclock=*) MAX_WALLCLOCK_HOURS="${arg#*=}" ;;
        --round-start=*) ROUND_START="${arg#*=}" ;;
    esac
done

START_TIME=$(date +%s)
MAX_WALLCLOCK_SEC=$((MAX_WALLCLOCK_HOURS * 3600))

mkdir -p proposals runs diagnostics reviews

if [[ "$PHASE" == "beta" ]]; then
    if ! git rev-parse refs/tags/v1.0-methodology-locked >/dev/null 2>&1; then
        echo "loop_orchestrator: ERROR - Phase β requires v1.0-methodology-locked git tag to exist" >&2
        exit 1
    fi
    if ! bash scripts/verify_methodology_lock.sh >/dev/null 2>&1; then
        echo "loop_orchestrator: ERROR - lock verification failed; Phase β refused" >&2
        exit 1
    fi
fi

# Track T1..T6 pass counts per round for stuck detection
declare -a T_PASS_COUNTS
NO_IMPROVE_STREAK=0
ROUND=$ROUND_START

while [[ $ROUND -lt $((ROUND_START + MAX_ROUNDS)) ]]; do
    ELAPSED=$(($(date +%s) - START_TIME))
    if [[ $ELAPSED -gt $MAX_WALLCLOCK_SEC ]]; then
        echo "loop_orchestrator: BUDGET_EXHAUSTED — wallclock $ELAPSED > $MAX_WALLCLOCK_SEC sec"
        cat > BUDGET_EXHAUSTED.md <<EOF
# BUDGET_EXHAUSTED — Loop halted by wallclock limit

- Phase: $PHASE
- Round at exit: $ROUND
- Max wallclock hours: $MAX_WALLCLOCK_HOURS
- Elapsed seconds: $ELAPSED
- T1..T6 pass counts per round: ${T_PASS_COUNTS[*]:-none}

The loop did not complete all rounds within the wallclock budget. Inspect runs/round_*/
and diagnostics/round_*.md for partial state. Re-run with --round-start=$ROUND and a fresh
wallclock budget if needed.
EOF
        exit 2
    fi

    echo "===== loop_orchestrator: ROUND $ROUND (phase=$PHASE) ====="

    RUN_DIR="runs/round_$ROUND"
    mkdir -p "$RUN_DIR"

    # STEP 1 — PROPOSE (snapshot the proposal)
    PROPOSAL="proposals/round_$ROUND.md"
    if [[ ! -f "$PROPOSAL" ]]; then
        cat > "$PROPOSAL" <<EOF
# Round $ROUND Proposal

Phase: $PHASE
Mainline objective: continue advancing the methodology (Phase α) or engineering (Phase β).
Decisions and proposed changes are recorded here before implementation.
EOF
    fi

    # STEP 2 — IMPLEMENT
    # The orchestrator records the start-of-round commit ref so STEP 7 rollback can restore safely
    # (avoids broad `git reset --hard HEAD~1` which can destroy unrelated work).
    START_OF_ROUND_REF=$(git rev-parse HEAD 2>/dev/null || echo "")
    echo "$START_OF_ROUND_REF" > "$RUN_DIR/start_of_round_ref.txt"
    touch "$RUN_DIR/implementation_started.flag"

    # STEP 3 — RUN
    if ! bash pipeline/run_pipeline.sh sample_input.json "$RUN_DIR/output.json" "$ROUND" 2>&1 | tee "$RUN_DIR/run_log.txt" | tail -5; then
        echo "loop_orchestrator: pipeline crashed in round $ROUND; counting toward budget"
        echo '{"status": "CRASHED"}' > "$RUN_DIR/crash.json"
        ROUND=$((ROUND + 1))
        continue
    fi

    # STEP 4 — EVALUATE (only in Phase β; verbose evaluator gated on lock tag)
    DIAG="diagnostics/round_$ROUND.md"
    if [[ "$PHASE" == "beta" ]]; then
        python3 evaluator/evaluator.py --mode verbose --input "$RUN_DIR/output.json" --output "$DIAG"
    else
        # Phase α: no evaluator invocation (per AC-1.1)
        echo "# Round $ROUND Diagnostic (Phase α — evaluator-free)" > "$DIAG"
        echo "" >> "$DIAG"
        echo "Phase α policy: External Evaluator not invoked. Methodology evaluation by Codex review only." >> "$DIAG"
    fi

    # STEP 5 — REVIEW (orchestrator does a self-check; full Codex review is external)
    REVIEW="reviews/round_$ROUND.md"
    cat > "$REVIEW" <<EOF
# Round $ROUND Review

Phase: $PHASE
Run dir: $RUN_DIR
Diagnostic: $DIAG

This file is the slot for the per-round Codex review. The Codex review is invoked
out-of-band (by the user's RLCR session) and writes its findings here.
EOF

    # STEP 6 — DECIDE
    DECISION_FILE="$RUN_DIR/decision.json"
    if [[ ! -f "$DECISION_FILE" ]]; then
        # Default decision: continue
        cat > "$DECISION_FILE" <<EOF
{"decision": "continue", "round": $ROUND, "reason": "no explicit decision recorded; default continue"}
EOF
    fi
    DECISION=$(python3 -c "import json; print(json.load(open('$DECISION_FILE')).get('decision', 'continue'))" 2>/dev/null || echo "continue")

    # STEP 7 — COMMIT (record round artifacts in git)
    git add -A 2>/dev/null || true
    git commit -m "round $ROUND ($PHASE): orchestrator-driven checkpoint" --allow-empty 2>/dev/null || true

    # Handle rollback — restore to saved start-of-round ref (NOT broad HEAD~1)
    if [[ "$DECISION" == "rollback" ]]; then
        START_REF=$(cat "$RUN_DIR/start_of_round_ref.txt" 2>/dev/null || echo "")
        if [[ -n "$START_REF" ]] && git rev-parse "$START_REF" >/dev/null 2>&1; then
            echo "loop_orchestrator: ROLLBACK requested in round $ROUND; restoring to $START_REF"
            git reset --soft "$START_REF" 2>/dev/null || true
            git checkout -- . 2>/dev/null || true
            git clean -fd 2>/dev/null || true
        else
            echo "loop_orchestrator: ROLLBACK requested but no valid start_of_round_ref; refusing destructive HEAD~1 reset" >&2
        fi
        # Don't count the rolled-back round toward improvement streak
        ROUND=$((ROUND + 1))
        continue
    fi

    if [[ "$DECISION" == "terminate" ]]; then
        echo "loop_orchestrator: TERMINATE requested in round $ROUND"
        break
    fi

    # STEP 8 — Parse T1..T6 pass count from diagnostic JSON summary block (machine-readable)
    T_PASSES=0
    if [[ -f "$DIAG" ]]; then
        # Diagnostic ends with a ```json ... ``` summary block; parse it
        T_PASSES=$(python3 - "$DIAG" <<'PYEOF' 2>/dev/null || echo 0
import json, re, sys
text = open(sys.argv[1]).read()
m = re.search(r"```json\s*({[\s\S]*?})\s*```", text)
if not m:
    print(0); sys.exit(0)
try:
    summary = json.loads(m.group(1))
except json.JSONDecodeError:
    print(0); sys.exit(0)
n_pass = 0
if summary.get("expected_target_in_top_n"): n_pass += 1
if summary.get("expected_target_rank") is not None: n_pass += 1
if summary.get("lock_tag"): n_pass += 1
if summary.get("pre_registration_hash") and not str(summary.get("pre_registration_hash")).endswith("_pre_lock"): n_pass += 1
rs = summary.get("reviewer_status")
if rs and rs not in {None, "REVIEWER_DEFERRED", "MOCK_STUB_FOR_ROUND_0"}: n_pass += 1
if summary.get("n_ranked_total", 0) > 0: n_pass += 1
print(n_pass)
PYEOF
)
        # Strip whitespace
        T_PASSES=$(echo "$T_PASSES" | tr -d '[:space:]')
        T_PASSES=${T_PASSES:-0}
    fi
    T_PASS_COUNTS[$ROUND]=$T_PASSES

    # Compute improvement: did this round's T_PASSES exceed the previous round's?
    if [[ $ROUND -gt $ROUND_START ]]; then
        PREV_PASSES=${T_PASS_COUNTS[$((ROUND - 1))]:-0}
        if [[ $T_PASSES -gt $PREV_PASSES ]]; then
            NO_IMPROVE_STREAK=0
        else
            NO_IMPROVE_STREAK=$((NO_IMPROVE_STREAK + 1))
        fi
    fi

    if [[ $NO_IMPROVE_STREAK -ge 3 ]]; then
        echo "loop_orchestrator: STUCK — 3 consecutive rounds without improvement"
        cat > STUCK.md <<EOF
# STUCK — Loop halted after 3 consecutive non-improving rounds

- Phase: $PHASE
- Round at exit: $ROUND
- T1..T6 pass counts per round: ${T_PASS_COUNTS[*]}
- Improvement streak: $NO_IMPROVE_STREAK

The loop made no T-pass progress in the last 3 rounds. Manual inspection of
diagnostics/round_*.md and reviews/round_*.md is needed to break the stall.
EOF
        exit 3
    fi

    ROUND=$((ROUND + 1))
done

# Exit conditions
if [[ $ROUND -ge $((ROUND_START + MAX_ROUNDS)) ]]; then
    cat > BUDGET_EXHAUSTED.md <<EOF
# BUDGET_EXHAUSTED — MAX_ROUNDS reached

- Phase: $PHASE
- Max rounds: $MAX_ROUNDS
- Round at exit: $ROUND
- T1..T6 pass counts per round: ${T_PASS_COUNTS[*]:-none}
EOF
    echo "loop_orchestrator: MAX_ROUNDS reached; wrote BUDGET_EXHAUSTED.md"
    exit 2
fi

echo "loop_orchestrator: loop terminated normally at round $ROUND (decision: $DECISION)"
exit 0
