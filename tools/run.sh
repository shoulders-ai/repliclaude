#!/usr/bin/env bash
# Wrapper to always run Python scripts via the project venv.
# Usage: bash tools/run.sh script.py [args...]
# All agents and scripts should use this instead of bare python3.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERROR: Virtual environment not found at $PROJECT_ROOT/.venv/"
    echo "Run: python3 -m venv $PROJECT_ROOT/.venv && $PROJECT_ROOT/.venv/bin/pip install -r $PROJECT_ROOT/requirements.txt"
    exit 1
fi

exec "$VENV_PYTHON" "$@"
