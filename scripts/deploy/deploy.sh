#!/usr/bin/env bash
set -euo pipefail

: "${IMAGE_TAG:?IMAGE_TAG is required}"
: "${REGISTRY:?REGISTRY is required}"

export COMPOSE_PROJECT_NAME=trainerhub
export BACKEND_IMAGE="${REGISTRY}/trainerhub-backend:${IMAGE_TAG}"
export FRONTEND_IMAGE="${REGISTRY}/trainerhub-frontend:${IMAGE_TAG}"

docker compose pull backend frontend worker beat
docker compose up -d postgres redis
docker compose run --rm backend python manage.py check --deploy --fail-level WARNING
docker compose run --rm backend python manage.py check_production_readiness --summary-only --fail-on-degraded
docker compose run --rm release
docker compose up -d backend worker beat flower frontend nginx
bash scripts/smoke/runtime.sh
