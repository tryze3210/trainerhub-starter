#!/usr/bin/env bash
set -euo pipefail

cd backend
python -m compileall .
pytest
flake8 .
mypy .
