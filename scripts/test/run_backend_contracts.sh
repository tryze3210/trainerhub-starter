#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
export DJANGO_SETTINGS_MODULE=config.settings_test
pytest backend/tests/contracts -q
