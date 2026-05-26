#!/usr/bin/env bash
# Run all 5 anti-bias mechanisms.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPELINE_ROOT="$(dirname "$DIR")"

echo "run_suite: starting anti-bias gauntlet..."

python3 "$DIR/loo_ablation.py" || exit 1
python3 "$DIR/negative_controls.py" || exit 1
python3 "$DIR/literature_blinded.py" || exit 1
python3 "$DIR/cross_biobank_mr.py" || exit 1
python3 "$DIR/permutation_test.py" || exit 1
python3 "$DIR/validate_suite_output.py" || exit 1

echo "run_suite: all 5 mechanisms complete"
exit 0
