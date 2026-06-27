#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

echo "== backend syntax =="
python -m compileall backend

echo "== backend django checks =="
(
  cd backend
  python manage.py check
  python manage.py check --deploy --fail-level WARNING
  python manage.py makemigrations --check --dry-run
)

echo "== backend tests =="
(
  cd backend
  pytest
)

echo "== backend contract tests =="
(
  cd backend
  pytest tests/contracts
)

echo "== production readiness =="
(
  cd backend
  python manage.py check_production_readiness --json --fail-on-degraded
)

echo "== backend dependency integrity =="
python -m pip check

echo "== frontend checks =="
(
  cd frontend
  npm ci
  npm run typecheck
  npm run build
  npm run test:contracts
  npm audit --audit-level=high
)

echo "production gate passed"
