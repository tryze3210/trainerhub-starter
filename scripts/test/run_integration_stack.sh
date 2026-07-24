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

cd "$ROOT_DIR"
docker compose -f docker-compose.test.yml up -d
trap 'docker compose -f docker-compose.test.yml down -v' EXIT
export DJANGO_SETTINGS_MODULE=config.settings.test
"$PYTHON_BIN" -m pytest backend/tests/integration -q
