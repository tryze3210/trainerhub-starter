#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
cp -n .env.example .env || true
python scripts/bootstrap/seed_demo.py
printf 'Local bootstrap scaffold completed.
'
