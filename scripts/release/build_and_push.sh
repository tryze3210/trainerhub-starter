#!/usr/bin/env bash
set -euo pipefail

: "${REGISTRY:?REGISTRY is required}"
: "${IMAGE_TAG:?IMAGE_TAG is required}"

BACKEND_IMAGE="${REGISTRY}/trainerhub-backend:${IMAGE_TAG}"
FRONTEND_IMAGE="${REGISTRY}/trainerhub-frontend:${IMAGE_TAG}"

docker build -f deploy/backend/Dockerfile -t "${BACKEND_IMAGE}" .
docker build -f deploy/frontend/Dockerfile -t "${FRONTEND_IMAGE}" .
docker push "${BACKEND_IMAGE}"
docker push "${FRONTEND_IMAGE}"

echo "Published ${BACKEND_IMAGE}"
echo "Published ${FRONTEND_IMAGE}"
