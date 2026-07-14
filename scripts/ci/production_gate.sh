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
export DATABASE_URL="${QUALITY_DATABASE_URL:-}"

echo "== backend syntax =="
"$PYTHON_BIN" -m compileall -q backend/apps backend/common backend/config backend/scripts backend/manage.py

echo "== backend django checks =="
(
  cd backend
  "$PYTHON_BIN" manage.py check
  (
    export DEBUG="${DEBUG:-0}"
    export SECRET_KEY="${SECRET_KEY:-trainerhub-production-gate-secret-key-with-safe-length-v167}"
    export ALLOWED_HOSTS="${ALLOWED_HOSTS:-trainerhub.local,localhost,127.0.0.1}"
    export CSRF_TRUSTED_ORIGINS="${CSRF_TRUSTED_ORIGINS:-https://trainerhub.local,http://localhost:8080}"
    export CORS_ALLOWED_ORIGINS="${CORS_ALLOWED_ORIGINS:-https://trainerhub.local,http://localhost:8080}"
    export SECURE_SSL_REDIRECT="${SECURE_SSL_REDIRECT:-1}"
    export SESSION_COOKIE_SECURE="${SESSION_COOKIE_SECURE:-1}"
    export CSRF_COOKIE_SECURE="${CSRF_COOKIE_SECURE:-1}"
    export SECURE_HSTS_SECONDS="${SECURE_HSTS_SECONDS:-31536000}"
    export SECURE_HSTS_INCLUDE_SUBDOMAINS="${SECURE_HSTS_INCLUDE_SUBDOMAINS:-1}"
    export SECURE_HSTS_PRELOAD="${SECURE_HSTS_PRELOAD:-1}"
    "$PYTHON_BIN" manage.py check --deploy --fail-level WARNING
  )
  "$PYTHON_BIN" manage.py makemigrations --check --dry-run
)

echo "== backend tests =="
(
  cd backend
  "$PYTHON_BIN" -m pytest
)

echo "== backend contract tests =="
(
  cd backend
  "$PYTHON_BIN" -m pytest tests/contracts
)

echo "== production readiness =="
(
  cd backend
  "$PYTHON_BIN" manage.py check_production_readiness --summary-only --fail-on-degraded
)

echo "== backend dependency integrity =="
"$PYTHON_BIN" -m pip check

echo "== frontend checks =="
(
  bash "$ROOT_DIR/scripts/quality/frontend_check.sh"
  cd "$ROOT_DIR/frontend"
  npm audit --audit-level=high
)

echo "production gate passed"
