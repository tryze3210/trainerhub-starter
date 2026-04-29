#!/usr/bin/env bash
set -euo pipefail

: "${IMAGE_TAG:?IMAGE_TAG is required}"

export COMPOSE_PROJECT_NAME=trainerhub

docker compose pull backend frontend worker beat
docker compose up -d postgres redis
docker compose run --rm backend python backend/manage.py migrate
docker compose up -d backend worker beat flower frontend nginx
bash scripts/smoke/runtime.sh
