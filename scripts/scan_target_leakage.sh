#!/usr/bin/env bash
# scan_target_leakage.sh - Scans Pipeline-side source for forbidden target identifiers.
#
# Usage: scan_target_leakage.sh [PATH_TO_SCAN]
#   Default scan root: pipeline/
#   Always excludes: evaluator/ (legitimate location for target-specific logic)
#   Always excludes: .git/, .humanize/, references/, data_sources/snapshots/ (data)
#
# Exit codes:
#   0 - no forbidden identifiers found in scanned source
#   1 - one or more forbidden identifiers found (leakage detected)
#   2 - usage / invocation error

set -euo pipefail

SCAN_ROOT="${1:-pipeline}"

if [[ ! -d "$SCAN_ROOT" ]]; then
    echo "scan_target_leakage: scan root not found: $SCAN_ROOT" >&2
    exit 2
fi

# Forbidden identifiers: gene symbols, aliases, and the Ensembl gene ID
FORBIDDEN_PATTERNS=(
    "GDF15"
    "GFRAL"
    "MIC-1"
    "MIC1"
    "NAG-1"
    "NAG1"
    "ENSG00000130513"
)

# Excluded directories (matched by directory NAME at any depth, per grep --exclude-dir behavior)
EXCLUDE_DIRS=(
    "snapshots"
    ".humanize"
    ".git"
    "__pycache__"
    "node_modules"
    ".cache"
)

EXCLUDE_ARGS=()
for d in "${EXCLUDE_DIRS[@]}"; do
    EXCLUDE_ARGS+=(--exclude-dir="$d")
done
# Scan only SOURCE files (Python, shell, Markdown text). Skip derived data (.tsv, .json), the forbidden-list config, and binary artifacts.
INCLUDE_ARGS=(--include="*.py" --include="*.sh" --include="*.md" --include="*.txt")
EXCLUDE_FILES=(--exclude="FORBIDDEN_TARGET_NAMES.txt" --exclude="candidate_universe.tsv" --exclude="_scores_*.tsv" --exclude="*.json")

HITS_FOUND=0
TOTAL_HITS=0

echo "scan_target_leakage: scanning $SCAN_ROOT for forbidden target identifiers..."

for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
    # Case-insensitive grep with line numbers; restrict to source extensions; suppress missing-file errors
    if hits=$(grep -rni "${INCLUDE_ARGS[@]}" "${EXCLUDE_FILES[@]}" "${EXCLUDE_ARGS[@]}" "$pattern" "$SCAN_ROOT" 2>/dev/null); then
        if [[ -n "$hits" ]]; then
            HITS_FOUND=1
            count=$(echo "$hits" | wc -l | tr -d ' ')
            TOTAL_HITS=$((TOTAL_HITS + count))
            echo ""
            echo "FORBIDDEN PATTERN '$pattern' found in $count location(s):"
            echo "$hits" | sed 's/^/    /'
        fi
    fi
done

echo ""
if [[ "$HITS_FOUND" -eq 0 ]]; then
    echo "scan_target_leakage: PASS - no forbidden identifiers found in $SCAN_ROOT"
    exit 0
else
    echo "scan_target_leakage: FAIL - $TOTAL_HITS forbidden identifier match(es) in $SCAN_ROOT"
    echo "scan_target_leakage: this scan is required by AC-2/AC-3/AC-4/AC-5/AC-6 to enforce target-blind Pipeline code"
    exit 1
fi
