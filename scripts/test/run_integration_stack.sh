#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
docker compose -f docker-compose.test.yml up -d
trap 'docker compose -f docker-compose.test.yml down -v' EXIT
export DJANGO_SETTINGS_MODULE=config.settings_test
pytest backend/tests/integration -q
