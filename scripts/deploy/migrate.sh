#!/usr/bin/env bash
set -euo pipefail

: "${IMAGE_TAG:?IMAGE_TAG is required}"
: "${REGISTRY:?REGISTRY is required}"

export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-trainerhub}"
export BACKEND_IMAGE="${REGISTRY}/trainerhub-backend:${IMAGE_TAG}"

docker compose run --rm backend python manage.py check --deploy --fail-level WARNING
docker compose run --rm backend python manage.py check_production_readiness --summary-only --fail-on-degraded
docker compose run --rm release
