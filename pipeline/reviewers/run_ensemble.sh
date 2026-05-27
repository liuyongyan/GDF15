#!/usr/bin/env bash
# run_ensemble.sh — Invoke the six-persona reviewer ensemble.
#
# Usage: run_ensemble.sh <round_number> <input_summary_path> <output_dir>
#
# Per-persona LLM invocation flow:
#   1. Compute deterministic backbone assignment (codex or gemini) from round seed.
#   2. For each persona, compute cache key = SHA1(persona_prompt || input_summary).
#   3. If cache hit at runs/reviewer_cache/<key>.json → use it.
#   4. Else invoke humanize wrapper (ask-codex.sh / ask-gemini.sh) with prompt+input.
#      - On 429/rate-limit/auth-error: retry on alternate backbone.
#      - If both backbones fail → record per-persona status and fall through.
#   5. Wrap response in per-persona structured JSON.
#   6. Aggregate all six personas into meta_review.
#   7. If all six succeeded (cache or live) → REGULAR mode output.
#      If ≥1 persona failed both backbones AND cache → REVIEWER_DEFERRED + RATE_LIMITED.md.

set -euo pipefail

ROUND_NUMBER="${1:-0}"
INPUT_SUMMARY="${2:-}"
OUTPUT_DIR="${3:-runs/round_$ROUND_NUMBER}"

if [[ -z "$INPUT_SUMMARY" ]] || [[ ! -f "$INPUT_SUMMARY" ]]; then
    echo "run_ensemble: ERROR - input summary not found: $INPUT_SUMMARY" >&2
    exit 2
fi

mkdir -p "$OUTPUT_DIR"
CACHE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/runs/reviewer_cache"
mkdir -p "$CACHE_DIR"
REVIEWERS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUMANIZE_SCRIPTS="/Users/yliu/.claude/plugins/cache/PolyArch/humanize/1.16.0/scripts"

PERSONAS=(R1_molecular_biologist R2_clinical_translator R3_geneticist_biostatistician R4_pharmacologist R5_ai_methods_reviewer R6_editor)

# 1. Deterministic backbone assignment
ASSIGNMENT_JSON="$OUTPUT_DIR/reviewer_backbone_assignment.json"
declare -a ASSIGNED_BACKBONES
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
    ASSIGNED_BACKBONES[$i]="$backbone"
    sep=""
    if [[ $i -ne $last ]]; then sep=","; fi
    echo "    \"$persona\": \"$backbone\"$sep" >> "$ASSIGNMENT_JSON"
done
echo "  }" >> "$ASSIGNMENT_JSON"
echo "}" >> "$ASSIGNMENT_JSON"

# 2-6. Per-persona invocation
invoke_backbone() {
    # $1 = backbone (codex|gemini); $2 = combined prompt; $3 = persona; $4 = output_file
    local backbone="$1" prompt="$2" persona="$3" out="$4"
    if [[ "$backbone" == "codex" ]]; then
        if ! command -v codex >/dev/null 2>&1; then return 2; fi
        if [[ ! -x "$HUMANIZE_SCRIPTS/ask-codex.sh" ]]; then return 2; fi
        local timeout_sec=90
        if "$HUMANIZE_SCRIPTS/ask-codex.sh" --codex-timeout "$timeout_sec" "$prompt" > "$out" 2>&1; then
            return 0
        fi
        return 1
    elif [[ "$backbone" == "gemini" ]]; then
        if ! command -v gemini >/dev/null 2>&1; then return 2; fi
        if [[ ! -x "$HUMANIZE_SCRIPTS/ask-gemini.sh" ]]; then return 2; fi
        local timeout_sec=90
        if "$HUMANIZE_SCRIPTS/ask-gemini.sh" --gemini-timeout "$timeout_sec" "$prompt" > "$out" 2>&1; then
            return 0
        fi
        return 1
    fi
    return 2
}

PER_PERSONA_DIR="$OUTPUT_DIR/per_persona"
mkdir -p "$PER_PERSONA_DIR"

input_hash=$(shasum "$INPUT_SUMMARY" | awk '{print $1}')

declare -a PERSONA_STATUS
declare -a PERSONA_BACKBONE_USED
declare -a PERSONA_TEXT_PATH
declare -a PERSONA_PROMPT_HASH

any_fail=0
any_real_succ=0
any_cache_hit=0
real_call_attempted=0

# Provenance TSV consumed by build_per_persona_json. Reset on each invocation.
PROVENANCE_TSV="$PER_PERSONA_DIR/_provenance.tsv"
: > "$PROVENANCE_TSV"

for i in "${!PERSONAS[@]}"; do
    persona="${PERSONAS[$i]}"
    primary="${ASSIGNED_BACKBONES[$i]}"
    if [[ "$primary" == "codex" ]]; then alt="gemini"; else alt="codex"; fi

    prompt_file="$REVIEWERS_DIR/${persona}.md"
    if [[ ! -f "$prompt_file" ]]; then
        PERSONA_STATUS[$i]="MISSING_PROMPT"
        PERSONA_BACKBONE_USED[$i]="none"
        PERSONA_TEXT_PATH[$i]=""
        any_fail=1
        continue
    fi

    prompt_text=$(cat "$prompt_file")
    input_text=$(cat "$INPUT_SUMMARY")
    combined="$prompt_text

INPUT SUMMARY FOR THIS ROUND:
$input_text"
    prompt_hash=$(printf "%s" "$combined" | shasum | awk '{print $1}')
    cache_key="${persona}_${prompt_hash}"
    cache_path="$CACHE_DIR/${cache_key}.txt"
    PERSONA_PROMPT_HASH[$i]="$prompt_hash"

    out_path="$PER_PERSONA_DIR/${persona}.txt"

    # 3. cache lookup
    if [[ -f "$cache_path" ]]; then
        cp "$cache_path" "$out_path"
        PERSONA_STATUS[$i]="CACHE_HIT"
        PERSONA_BACKBONE_USED[$i]="cache"
        PERSONA_TEXT_PATH[$i]="$out_path"
        any_cache_hit=1
        echo "run_ensemble: $persona — cache hit"
        continue
    fi

    # 4a. try primary backbone (live)
    real_call_attempted=1
    if invoke_backbone "$primary" "$combined" "$persona" "$out_path"; then
        cp "$out_path" "$cache_path"
        PERSONA_STATUS[$i]="REAL_LIVE_PRIMARY"
        PERSONA_BACKBONE_USED[$i]="$primary"
        PERSONA_TEXT_PATH[$i]="$out_path"
        any_real_succ=1
        echo "run_ensemble: $persona — live $primary OK"
        continue
    fi
    primary_rc=$?

    # 4b. try alternate backbone (live)
    if invoke_backbone "$alt" "$combined" "$persona" "$out_path"; then
        cp "$out_path" "$cache_path"
        PERSONA_STATUS[$i]="REAL_LIVE_ALTERNATE"
        PERSONA_BACKBONE_USED[$i]="$alt"
        PERSONA_TEXT_PATH[$i]="$out_path"
        any_real_succ=1
        echo "run_ensemble: $persona — live $alt OK (primary $primary failed)"
        continue
    fi

    # Both backbones failed — record per-persona failure
    PERSONA_STATUS[$i]="BOTH_BACKBONES_FAILED"
    PERSONA_BACKBONE_USED[$i]="none"
    PERSONA_TEXT_PATH[$i]=""
    any_fail=1
    echo "run_ensemble: $persona — both backbones failed (primary $primary, alternate $alt)" >&2
done

# Emit per-persona provenance TSV consumed by build_per_persona_json
for i in "${!PERSONAS[@]}"; do
    persona="${PERSONAS[$i]}"
    status="${PERSONA_STATUS[$i]:-UNKNOWN}"
    backbone="${PERSONA_BACKBONE_USED[$i]:-unknown}"
    phash="${PERSONA_PROMPT_HASH[$i]:-}"
    printf "%s\t%s\t%s\t%s\t%s\n" "$persona" "$status" "$backbone" "$phash" "$input_hash" >> "$PROVENANCE_TSV"
done

VERDICT_JSON="$OUTPUT_DIR/reviewer_ensemble_verdict.json"
LOCK_TAG_EXISTS=0
git rev-parse refs/tags/v1.0-methodology-locked >/dev/null 2>&1 && LOCK_TAG_EXISTS=1

# Construct per_persona JSON wrapping each persona's raw output text + parsed JSON
build_per_persona_json() {
    python3 - "$PER_PERSONA_DIR" "${PERSONAS[@]}" <<'PYEOF'
import json, sys, os, re, hashlib

def parse_first_json_block(text: str):
    """Try to extract the first valid JSON object from text (possibly inside ```json fences)."""
    # Try fenced JSON first
    fenced = re.findall(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    for cand in fenced:
        try:
            return json.loads(cand)
        except (json.JSONDecodeError, ValueError):
            continue
    # Try to find a bare JSON object by scanning for balanced braces
    start = text.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{": depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    cand = text[start:i+1]
                    try:
                        return json.loads(cand)
                    except (json.JSONDecodeError, ValueError):
                        break
        start = text.find("{", start + 1)
    return None


per_dir = sys.argv[1]
personas = sys.argv[2:]
# Read provenance map written by the shell loop (one line per persona):
#   PERSONA<TAB>STATUS<TAB>BACKBONE_USED<TAB>PROMPT_HASH<TAB>INPUT_HASH
provenance = {}
prov_path = os.path.join(per_dir, "_provenance.tsv")
if os.path.exists(prov_path):
    for line in open(prov_path):
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 5:
            provenance[parts[0]] = {
                "status": parts[1],
                "backbone_used": parts[2],
                "prompt_hash": parts[3],
                "input_hash": parts[4],
            }
out = {}
for p in personas:
    prov = provenance.get(p, {
        "status": "UNKNOWN",
        "backbone_used": "unknown",
        "prompt_hash": "",
        "input_hash": "",
    })
    txt_path = os.path.join(per_dir, f"{p}.txt")
    if os.path.exists(txt_path):
        with open(txt_path, "r") as f:
            text = f.read()
        parsed = parse_first_json_block(text)
        blockers_count = 0
        critiques = []
        global_notes = []
        if parsed and isinstance(parsed, dict):
            blockers_count = int(parsed.get("blockers_count", 0) or 0)
            crit = parsed.get("critiques", [])
            if isinstance(crit, list):
                critiques = crit
            notes = parsed.get("global_methodology_notes", [])
            if isinstance(notes, list):
                global_notes = notes
        text_hash = hashlib.sha1(text.encode("utf-8")).hexdigest()
        out[p] = {
            "persona": p,
            "status": prov["status"],
            "backbone_used": prov["backbone_used"],
            "prompt_hash": prov["prompt_hash"],
            "input_hash": prov["input_hash"],
            "raw_text": text[:8000],
            "raw_text_sha1": text_hash,
            "parsed_json_present": parsed is not None,
            "blockers_count": blockers_count,
            "critiques": critiques,
            "global_methodology_notes": global_notes,
        }
    else:
        out[p] = {
            "persona": p,
            "status": prov["status"],
            "backbone_used": prov["backbone_used"],
            "prompt_hash": prov["prompt_hash"],
            "input_hash": prov["input_hash"],
            "missing": True,
            "blockers_count": 0,
            "critiques": [],
        }
print(json.dumps(out, indent=2, sort_keys=True))
PYEOF
}

# Decide overall verdict
if [[ $any_fail -eq 1 ]]; then
    # Per-persona failure → REVIEWER_DEFERRED with explicit evidence + parsed-blocker aggregation
    fail_personas=()
    fail_backbones_set=()
    for i in "${!PERSONAS[@]}"; do
        if [[ "${PERSONA_STATUS[$i]}" == "BOTH_BACKBONES_FAILED" ]] || [[ "${PERSONA_STATUS[$i]}" == "MISSING_PROMPT" ]]; then
            fail_personas+=("\"${PERSONAS[$i]}\"")
            fail_backbones_set+=("codex" "gemini")
        fi
    done
    fail_personas_json=$(IFS=,; echo "${fail_personas[*]}")
    reason="Live LLM invocation attempted for round $ROUND_NUMBER. Per-persona failure(s) recorded. ${#fail_personas[@]} of ${#PERSONAS[@]} personas failed both primary and alternate backbones (and had no cache entry)."
    # Write RATE_LIMITED.md (proper evidence)
    cat > "$OUTPUT_DIR/RATE_LIMITED.md" <<EOF
# RATE_LIMITED — Reviewer ensemble could not complete round $ROUND_NUMBER

## Affected Personas
$(for p in "${fail_personas[@]}"; do echo "- $p (BOTH_BACKBONES_FAILED)"; done)

## Affected Backbones
- codex (gpt-5.5) — primary or alternate failed
- gemini (gemini-3.1-pro-preview) — primary or alternate failed

## Remediation

1. **Switch to API billing** for Anthropic / OpenAI / Google by setting environment variables:
   \`\`\`bash
   export ANTHROPIC_API_KEY=sk-ant-api03-...  # if Claude rate-limited
   export OPENAI_API_KEY=sk-proj-...          # if Codex rate-limited
   export GEMINI_API_KEY=AIza...              # if Gemini rate-limited
   \`\`\`
   See https://console.anthropic.com, https://platform.openai.com, https://aistudio.google.com/apikey

2. **Verify CLI auth**:
   \`\`\`bash
   codex --version    # should be ≥0.133
   gemini --version   # should be ≥0.37
   \`\`\`

3. **Re-run** the ensemble for this round:
   \`\`\`bash
   REAL_LLM_REVIEW=1 bash pipeline/reviewers/run_ensemble.sh $ROUND_NUMBER $INPUT_SUMMARY $OUTPUT_DIR
   \`\`\`

   Cached personas (from prior successful runs) are skipped automatically; only failed personas are re-invoked.

## Cache Status
Cache directory: \`$CACHE_DIR\`
EOF
    per_persona_json=$(build_per_persona_json)
    python3 - "$VERDICT_JSON" "$ROUND_NUMBER" "$reason" "$fail_personas_json" "$per_persona_json" "$REVIEWERS_DIR" <<'PYEOF'
import json, sys
sys.path.insert(0, sys.argv[5])
from blocker_normalization import normalize_blockers
verdict_path, round_num, reason, fail_personas_json, per_persona_json, _reviewers_dir = sys.argv[1:7]
fail_personas = json.loads(f"[{fail_personas_json}]") if fail_personas_json.strip() else []
per_persona = json.loads(per_persona_json)
# Single shared normalization path (AC-5)
blockers_remaining = normalize_blockers(per_persona)
total_blockers = sum(int((p or {}).get("blockers_count", 0) or 0) for p in per_persona.values() if isinstance(p, dict))
doc = {
    "schema_version": "1.0",
    "round": int(round_num),
    "status": "REVIEWER_DEFERRED",
    "mode": "REVIEWER_DEFERRED",
    "reason": reason,
    "affected_personas": fail_personas,
    "affected_backbones": ["codex", "gemini"],
    "remediation": "Set ANTHROPIC_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY for API billing, verify CLI auth, re-run run_ensemble.sh; cached personas are auto-skipped.",
    "per_persona": per_persona,
    "meta_review": {
        "verdict": "deferred_with_partial_blockers" if total_blockers > 0 else "deferred",
        "consensus_blockers": [],
        "single_reviewer_blockers": blockers_remaining,
        "pipeline_methodology_concerns": [
            f"{len(fail_personas)} persona(s) failed all backbones; see RATE_LIMITED.md",
            f"Aggregated {total_blockers} parsed blocker(s) from personas that returned valid JSON",
        ],
        "cross_reviewer_agreement_summary": f"Partial — some personas unavailable; {total_blockers} parsed blockers preserved",
    },
    "blockers_remaining": blockers_remaining,
}
with open(verdict_path, "w") as f:
    json.dump(doc, f, indent=2, sort_keys=True)
PYEOF
    # Redact forbidden names from reviewer prose BEFORE the verdict is consumed downstream
    python3 "$REVIEWERS_DIR/redact_forbidden.py" "$VERDICT_JSON"
    echo "run_ensemble: REVIEWER_DEFERRED (some personas failed); see $OUTPUT_DIR/RATE_LIMITED.md"
    exit 0
fi

# All six personas have output (cache or live)
per_persona_json=$(build_per_persona_json)
mode="REGULAR"
status_msg="ALL_SIX_INVOKED"
if [[ $any_real_succ -eq 0 && $any_cache_hit -eq 1 ]]; then
    status_msg="ALL_SIX_FROM_CACHE"
fi

python3 - "$VERDICT_JSON" "$ROUND_NUMBER" "$mode" "$status_msg" "$per_persona_json" "$REVIEWERS_DIR" <<'PYEOF'
import json, sys
sys.path.insert(0, sys.argv[6])
from blocker_normalization import normalize_blockers
verdict_path, round_num, mode, status_msg, per_persona_json, _reviewers_dir = sys.argv[1:7]
per_persona = json.loads(per_persona_json)
# Single shared normalization path (AC-5) — same logic used in deferred mode
blockers_remaining = normalize_blockers(per_persona)
total_blockers_parsed = sum(int((p or {}).get("blockers_count", 0) or 0) for p in per_persona.values() if isinstance(p, dict))
# Use the propagated-blocker count for verdict labeling (not the raw parsed count,
# which may include "None"/empty placeholder blockers that normalization drops).
n_real_blockers = len(blockers_remaining)
verdict_label = "real_review_complete" if n_real_blockers == 0 else "blockers_present"
overall_status_label = "PASS" if n_real_blockers == 0 else "BLOCKERS_PRESENT"
total_blockers = n_real_blockers
doc = {
    "schema_version": "1.0",
    "round": int(round_num),
    "status": status_msg,
    "mode": mode,
    "verdict": verdict_label,
    "overall_status": overall_status_label,
    "per_persona": per_persona,
    "meta_review": {
        "verdict": verdict_label,
        "consensus_blockers": [],
        "single_reviewer_blockers": blockers_remaining,
        "pipeline_methodology_concerns": [],
        "cross_reviewer_agreement_summary": f"All 6 personas reviewed ({status_msg}); total parsed blockers across personas = {total_blockers}",
    },
    "blockers_remaining": blockers_remaining,
}
with open(verdict_path, "w") as f:
    json.dump(doc, f, indent=2, sort_keys=True)
PYEOF

# Redact forbidden names from reviewer prose BEFORE the verdict is consumed downstream
python3 "$REVIEWERS_DIR/redact_forbidden.py" "$VERDICT_JSON"
echo "run_ensemble: all six personas have output ($status_msg); wrote $VERDICT_JSON"
exit 0
