#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "$ROOT_DIR/frontend"

rm -rf .next-quality
npm ci
npm run typecheck
npm run test:contracts
NEXT_DIST_DIR=.next-quality npm run build
