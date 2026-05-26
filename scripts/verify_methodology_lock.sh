#!/usr/bin/env bash
# verify_methodology_lock.sh - Verifies methodology lock integrity.
#
# Behavior:
#   - If git tag v1.0-methodology-locked does NOT exist:
#       reports "not yet locked" and exits 0 (informational, not a failure pre-lock)
#   - If the tag exists AND pipeline/LOCKED_ARTIFACTS.json exists:
#       recomputes SHA256 for each listed artifact and compares against the locked hash
#       exits 0 if all forbidden-mutability artifacts match
#       exits 1 if any forbidden-mutability artifact differs from its locked hash
#   - If the tag exists but LOCKED_ARTIFACTS.json is missing or malformed:
#       exits 2 (configuration error)

set -euo pipefail

LOCK_TAG="${LOCK_TAG:-v1.0-methodology-locked}"
LOCKED_ARTIFACTS_JSON="pipeline/LOCKED_ARTIFACTS.json"

if ! git rev-parse "refs/tags/$LOCK_TAG" >/dev/null 2>&1; then
    echo "verify_methodology_lock: tag '$LOCK_TAG' not yet created (pre-lock state)"
    echo "verify_methodology_lock: methodology lock has not been performed yet; nothing to verify"
    exit 0
fi

if [[ ! -f "$LOCKED_ARTIFACTS_JSON" ]]; then
    echo "verify_methodology_lock: ERROR - tag '$LOCK_TAG' exists but $LOCKED_ARTIFACTS_JSON is missing" >&2
    echo "verify_methodology_lock: a valid lock requires both the tag and the manifest" >&2
    exit 2
fi

if ! command -v jq >/dev/null 2>&1; then
    echo "verify_methodology_lock: ERROR - jq is required to parse $LOCKED_ARTIFACTS_JSON" >&2
    exit 2
fi

if ! jq -e '.artifacts | type == "array"' "$LOCKED_ARTIFACTS_JSON" >/dev/null 2>&1; then
    echo "verify_methodology_lock: ERROR - $LOCKED_ARTIFACTS_JSON is malformed (missing 'artifacts' array)" >&2
    exit 2
fi

FAIL_COUNT=0
TOTAL=0

echo "verify_methodology_lock: tag '$LOCK_TAG' present; verifying SHA256 of locked artifacts..."

# Iterate artifacts
while IFS= read -r entry; do
    TOTAL=$((TOTAL + 1))
    path=$(echo "$entry" | jq -r '.path')
    locked_sha=$(echo "$entry" | jq -r '.sha256')
    mutability=$(echo "$entry" | jq -r '.mutability')
    purpose=$(echo "$entry" | jq -r '.purpose')

    if [[ ! -f "$path" ]]; then
        echo "  [$path] MISSING (was locked but no longer present) - mutability=$mutability"
        if [[ "$mutability" == "forbidden" ]]; then
            FAIL_COUNT=$((FAIL_COUNT + 1))
        fi
        continue
    fi

    current_sha=$(shasum -a 256 "$path" | awk '{print $1}')

    if [[ "$current_sha" == "$locked_sha" ]]; then
        echo "  [$path] OK - mutability=$mutability"
    else
        echo "  [$path] CHANGED - mutability=$mutability"
        echo "    locked:  $locked_sha"
        echo "    current: $current_sha"
        echo "    purpose: $purpose"
        if [[ "$mutability" == "forbidden" ]]; then
            FAIL_COUNT=$((FAIL_COUNT + 1))
        else
            echo "    (mutability=$mutability, change permitted with engineering_audit_note)"
        fi
    fi
done < <(jq -c '.artifacts[]' "$LOCKED_ARTIFACTS_JSON")

echo ""
echo "verify_methodology_lock: checked $TOTAL artifact(s)"
if [[ "$FAIL_COUNT" -eq 0 ]]; then
    echo "verify_methodology_lock: PASS - all forbidden-mutability artifacts match locked SHA256"
    exit 0
else
    echo "verify_methodology_lock: FAIL - $FAIL_COUNT forbidden-mutability artifact(s) changed after lock"
    exit 1
fi
