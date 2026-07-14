#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_BIN="${PYTHON:-$ROOT_DIR/backend/.venv/bin/python}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1 || ! "$PYTHON_BIN" --version >/dev/null 2>&1; then
  PYTHON_BIN="${PYTHON_FALLBACK:-python}"
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1 || ! "$PYTHON_BIN" --version >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi

cd "$ROOT_DIR/backend"

export DATABASE_URL="${QUALITY_DATABASE_URL:-}"

"$PYTHON_BIN" manage.py check
"$PYTHON_BIN" manage.py makemigrations --check --dry-run
"$PYTHON_BIN" -m pytest
"$PYTHON_BIN" -m flake8 .
"$PYTHON_BIN" -m mypy .
