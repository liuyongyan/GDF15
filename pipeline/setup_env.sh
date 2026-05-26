#!/usr/bin/env bash
# setup_env.sh — Provision Python virtual environment and install pinned deps.
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -d ".venv" ]]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -r pipeline/REQUIREMENTS.txt

echo "setup_env: virtualenv .venv ready; activate with 'source .venv/bin/activate'"
echo "setup_env: Round 0 uses only stdlib; pip install was a no-op."
