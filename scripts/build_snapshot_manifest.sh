#!/usr/bin/env bash
# build_snapshot_manifest.sh — Build SHA256 manifest for data snapshots.
set -euo pipefail
cd "$(dirname "$0")/.."

MANIFEST="pipeline/data_sources/SNAPSHOT_HASHES.txt"
{
    echo "# SHA256 hashes for cached data snapshots."
    echo "# Format: <sha256>  <relative-path>"
    echo "# Regenerate with: scripts/build_snapshot_manifest.sh"
    for f in pipeline/data_sources/snapshots/*.tsv; do
        sha=$(shasum -a 256 "$f" | awk '{print $1}')
        printf "%s %s\n" "$sha" "$f"
    done
} > "$MANIFEST"
echo "Wrote $MANIFEST"
