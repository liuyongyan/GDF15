#!/usr/bin/env bash
# preflight.sh — Verify environment before starting the overnight loop.
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

echo "=== preflight ==="
ERRORS=0

check() {
    local name="$1"; shift
    if "$@" >/dev/null 2>&1; then
        echo "  ✓ $name"
    else
        echo "  ✗ $name" >&2
        ERRORS=$((ERRORS + 1))
    fi
}

echo "1. Required tools:"
check "python3" python3 --version
check "jq" jq --version
check "git" git --version
check "shasum" command -v shasum
echo ""

echo "2. Optional tools (LLM CLIs):"
if command -v codex >/dev/null 2>&1; then echo "  ✓ codex"; else echo "  - codex (not found; reviewer ensemble will fall back)"; fi
if command -v gemini >/dev/null 2>&1; then echo "  ✓ gemini"; else echo "  - gemini (not found; reviewer ensemble will fall back)"; fi
echo ""

echo "3. Data snapshots:"
for f in opentargets_metabolic_associations.tsv gwas_catalog_metabolic_loci.tsv chembl_metabolic_targets.tsv literature_metabolic_genes.tsv uniprot_protein_classes.tsv; do
    if [[ -f "pipeline/data_sources/snapshots/$f" ]]; then
        echo "  ✓ $f"
    else
        echo "  ✗ $f (missing)" >&2
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

echo "4. Evaluator config:"
for f in evaluator/expected_answer.json evaluator/expected_thresholds.json; do
    if [[ -f "$f" ]]; then
        echo "  ✓ $f"
    else
        echo "  ✗ $f (missing — evaluator cannot run verbose mode)" >&2
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

echo "5. API credentials (optional; needed for live LLM in subsequent rounds):"
for env_var in ANTHROPIC_API_KEY OPENAI_API_KEY GEMINI_API_KEY; do
    if [[ -n "${!env_var:-}" ]]; then
        echo "  ✓ $env_var is set"
    else
        echo "  - $env_var is NOT set (subscription fallback only)"
    fi
done
echo ""

echo "6. Git state:"
if git diff --quiet && git diff --cached --quiet; then
    echo "  ✓ working tree clean"
else
    echo "  ✗ working tree has uncommitted changes (loop start requires clean tree)" >&2
    ERRORS=$((ERRORS + 1))
fi
echo ""

echo "6a. Snapshot integrity (SHA256 manifest):"
MANIFEST="pipeline/data_sources/SNAPSHOT_HASHES.txt"
if [[ -f "$MANIFEST" ]]; then
    snapshot_errors=0
    while IFS=' ' read -r expected_hash rel_path; do
        [[ -z "$expected_hash" || "$expected_hash" == \#* ]] && continue
        if [[ ! -f "$rel_path" ]]; then
            echo "  ✗ $rel_path (missing)" >&2
            snapshot_errors=$((snapshot_errors + 1))
            continue
        fi
        actual=$(shasum -a 256 "$rel_path" | awk '{print $1}')
        if [[ "$actual" == "$expected_hash" ]]; then
            echo "  ✓ $rel_path"
        else
            echo "  ✗ $rel_path (hash mismatch)" >&2
            snapshot_errors=$((snapshot_errors + 1))
        fi
    done < "$MANIFEST"
    if [[ $snapshot_errors -gt 0 ]]; then
        ERRORS=$((ERRORS + snapshot_errors))
    fi
else
    echo "  - SNAPSHOT_HASHES.txt absent; run scripts/build_snapshot_manifest.sh to generate"
fi
echo ""

echo "7. Disk space (project dir):"
df -h "$ROOT" | tail -1 | awk '{print "  " $4 " available"}'
echo ""

if [[ $ERRORS -eq 0 ]]; then
    echo "preflight: PASS"
    exit 0
else
    echo "preflight: FAIL ($ERRORS error(s))" >&2
    exit 1
fi
