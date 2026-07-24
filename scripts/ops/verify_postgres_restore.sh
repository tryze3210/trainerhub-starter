#!/usr/bin/env bash
set -euo pipefail

: "${BACKUP_FILE:?BACKUP_FILE is required}"
: "${RESTORE_DATABASE_URL:?RESTORE_DATABASE_URL is required}"
: "${RESTORE_TARGET_ISOLATED:?Set RESTORE_TARGET_ISOLATED=1 to confirm this is an isolated restore target}"

if [[ "$RESTORE_TARGET_ISOLATED" != "1" ]]; then
  echo "Refusing restore: RESTORE_TARGET_ISOLATED must be 1" >&2
  exit 1
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "Backup file not found: $BACKUP_FILE" >&2
  exit 1
fi

if ! command -v gzip >/dev/null 2>&1; then
  echo "gzip is required" >&2
  exit 1
fi

if ! command -v psql >/dev/null 2>&1; then
  echo "psql is required" >&2
  exit 1
fi

gzip -t "$BACKUP_FILE"
psql "$RESTORE_DATABASE_URL" --set ON_ERROR_STOP=1 --command "select current_database();"
gzip -cd "$BACKUP_FILE" | psql "$RESTORE_DATABASE_URL" --set ON_ERROR_STOP=1

if [[ "${RUN_DJANGO_CHECK:-0}" == "1" ]]; then
  ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
  PYTHON_BIN="${PYTHON:-$ROOT_DIR/backend/.venv/bin/python}"
  if ! command -v "$PYTHON_BIN" >/dev/null 2>&1 || ! "$PYTHON_BIN" --version >/dev/null 2>&1; then
    PYTHON_BIN="${PYTHON_FALLBACK:-python3}"
  fi
  (
    cd "$ROOT_DIR/backend"
    DATABASE_URL="$RESTORE_DATABASE_URL" "$PYTHON_BIN" manage.py check
    DATABASE_URL="$RESTORE_DATABASE_URL" "$PYTHON_BIN" manage.py check_production_readiness --summary-only --fail-on-degraded
  )
fi

echo "restore_verified=true"
