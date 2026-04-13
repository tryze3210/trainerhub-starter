# Testing runbook

## Local quick start
1. `python -m compileall backend`
2. `pytest backend/tests/contracts -q`
3. `pytest backend/tests/integration -q`
4. `cd frontend && npm run test:contracts`

## Integration stack
- start isolated services with `docker compose -f docker-compose.test.yml up -d`
- execute integration tests
- stop with `docker compose -f docker-compose.test.yml down -v`

## Seed/bootstrap
- generate demo payload with `python scripts/bootstrap/seed_demo.py`
- initialize local scaffold with `bash scripts/bootstrap/bootstrap_local.sh`
