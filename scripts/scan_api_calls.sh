#!/usr/bin/env bash
# scan_api_calls.sh - Best-effort static analysis to flag undocumented network calls.
#
# Looks for common HTTP client patterns in Pipeline-side code.
# Pipeline code may make live calls but each call must be logged to runs/round_N/api_calls.log.

set -euo pipefail

SCAN_ROOT="${1:-pipeline}"

if [[ ! -d "$SCAN_ROOT" ]]; then
    echo "scan_api_calls: scan root not found: $SCAN_ROOT" >&2
    exit 2
fi

PATTERNS=(
    "requests\\.get"
    "requests\\.post"
    "requests\\.put"
    "requests\\.delete"
    "urllib\\.request"
    "urllib\\.urlopen"
    "httpx\\."
    "aiohttp\\."
    "curl "
    "wget "
)

EXCLUDE_DIRS=(
    "snapshots"
    ".humanize"
    ".git"
    "__pycache__"
)

EXCLUDE_ARGS=()
for d in "${EXCLUDE_DIRS[@]}"; do
    EXCLUDE_ARGS+=(--exclude-dir="$d")
done

HITS_FOUND=0
echo "scan_api_calls: scanning $SCAN_ROOT for HTTP client patterns..."

for pattern in "${PATTERNS[@]}"; do
    if hits=$(grep -rnE "${EXCLUDE_ARGS[@]}" "$pattern" "$SCAN_ROOT" 2>/dev/null); then
        if [[ -n "$hits" ]]; then
            HITS_FOUND=1
            echo ""
            echo "Pattern '$pattern' found:"
            echo "$hits" | sed 's/^/    /'
        fi
    fi
done

echo ""
if [[ "$HITS_FOUND" -eq 0 ]]; then
    echo "scan_api_calls: no HTTP client patterns found"
    exit 0
else
    echo "scan_api_calls: HTTP client patterns found. Each call MUST be logged to runs/round_N/api_calls.log per AC-2.1."
    echo "scan_api_calls: this is informational, not a hard fail. Reviewer should verify logging."
    exit 0
fi
