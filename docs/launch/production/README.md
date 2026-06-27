# v120 — Production Launch Pack

This directory is the production launch documentation pack.

## Documents

- `deploy.md` — deploy procedure and post-deploy checks.
- `backup.md` — backup and restore requirements.
- `monitoring.md` — monitoring signals and alert routing.
- `admin.md` — admin/support/finance operations guide.
- `trainer.md` — trainer production guide.
- `student.md` — student production guide.

## Gates

- `bash scripts/ci/production_gate.sh`
- `bash scripts/ci/launch_gate.sh`
- `cd backend && python manage.py check_production_readiness --json --fail-on-degraded`
- `GET /api/v1/ops/admin/production-launch-pack/`

## Release State

- Project version: `v120-production-launch-pack`
- Previous stage: `v119-launch-candidate`
- Ship condition: production gate green, production readiness ok, staging validation complete.
