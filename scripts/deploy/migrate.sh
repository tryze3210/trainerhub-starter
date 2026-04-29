#!/usr/bin/env bash
set -euo pipefail

docker compose run --rm backend python backend/manage.py migrate
