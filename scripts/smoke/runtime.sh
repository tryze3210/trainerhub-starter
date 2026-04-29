#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"

curl -fsS "${BASE_URL}/api/v1/runtime/health/" >/dev/null
curl -fsS "${BASE_URL}/api/v1/runtime/readiness/" >/dev/null
curl -fsS "${BASE_URL}/api/v1/runtime/config/" >/dev/null

echo "Runtime smoke checks passed"
