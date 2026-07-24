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
    export APP_ENV="${APP_ENV:-production}"
    export DEBUG="${DEBUG:-0}"
    export SECRET_KEY="${SECRET_KEY:-trainerhub-production-gate-secret-key-with-safe-length-v167}"
    export ALLOWED_HOSTS="${ALLOWED_HOSTS:-trainerhub.local}"
    export API_BASE_URL="${API_BASE_URL:-https://api.trainerhub.local}"
    export FRONTEND_BASE_URL="${FRONTEND_BASE_URL:-https://trainerhub.local}"
    export CSRF_TRUSTED_ORIGINS="${CSRF_TRUSTED_ORIGINS:-https://trainerhub.local}"
    export CORS_ALLOWED_ORIGINS="${CORS_ALLOWED_ORIGINS:-https://trainerhub.local}"
    export DATABASE_URL="${DATABASE_URL:-postgres://trainerhub:trainerhub@postgres:5432/trainerhub}"
    export REDIS_URL="${REDIS_URL:-redis://redis:6379/0}"
    export CACHE_URL="${CACHE_URL:-redis://redis:6379/0}"
    export CELERY_BROKER_URL="${CELERY_BROKER_URL:-redis://redis:6379/1}"
    export CELERY_RESULT_BACKEND="${CELERY_RESULT_BACKEND:-redis://redis:6379/2}"
    export CELERY_TASK_ALWAYS_EAGER="${CELERY_TASK_ALWAYS_EAGER:-0}"
    export SENTRY_DSN="${SENTRY_DSN:-https://public@example.ingest.sentry.io/1}"
    export VK_CLOUD_ENDPOINT="${VK_CLOUD_ENDPOINT:-https://s3.trainerhub.local}"
    export VK_CLOUD_ACCESS_KEY="${VK_CLOUD_ACCESS_KEY:-trainerhub-production-gate-storage-access-key}"
    export VK_CLOUD_SECRET_KEY="${VK_CLOUD_SECRET_KEY:-trainerhub-production-gate-storage-secret-key}"
    export VK_S3_ENDPOINT_URL="${VK_S3_ENDPOINT_URL:-$VK_CLOUD_ENDPOINT}"
    export VK_S3_ACCESS_KEY_ID="${VK_S3_ACCESS_KEY_ID:-$VK_CLOUD_ACCESS_KEY}"
    export VK_S3_SECRET_ACCESS_KEY="${VK_S3_SECRET_ACCESS_KEY:-$VK_CLOUD_SECRET_KEY}"
    export VK_PRIVATE_BUCKET="${VK_PRIVATE_BUCKET:-trainerhub-production-gate-private}"
    export VK_PUBLIC_BUCKET="${VK_PUBLIC_BUCKET:-trainerhub-production-gate-public}"
    export EMAIL_BACKEND="${EMAIL_BACKEND:-django.core.mail.backends.smtp.EmailBackend}"
    export DEFAULT_FROM_EMAIL="${DEFAULT_FROM_EMAIL:-TrainerHub <no-reply@trainerhub.local>}"
    export EMAIL_HOST="${EMAIL_HOST:-smtp.trainerhub.local}"
    export SECURE_SSL_REDIRECT="${SECURE_SSL_REDIRECT:-1}"
    export SESSION_COOKIE_SECURE="${SESSION_COOKIE_SECURE:-1}"
    export CSRF_COOKIE_SECURE="${CSRF_COOKIE_SECURE:-1}"
    export SECURE_HSTS_SECONDS="${SECURE_HSTS_SECONDS:-31536000}"
    export SECURE_HSTS_INCLUDE_SUBDOMAINS="${SECURE_HSTS_INCLUDE_SUBDOMAINS:-1}"
    export SECURE_HSTS_PRELOAD="${SECURE_HSTS_PRELOAD:-1}"
    "$PYTHON_BIN" manage.py check --deploy --fail-level WARNING
  )
  "$PYTHON_BIN" manage.py makemigrations --check --dry-run
  "$PYTHON_BIN" -m pytest tests/test_error_tracking_contract.py
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
