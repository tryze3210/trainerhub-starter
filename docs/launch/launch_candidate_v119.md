# v119 — Launch Candidate

This document marks the TrainerHub v119 launch candidate package.

## Project Version

- Project version file: `VERSION`
- Current project version: `v119-launch-candidate`
- Release candidate API: `GET /api/v1/ops/admin/launch-candidate/`

## Smoke Checklist

- Backend quality: `cd backend && python manage.py check && python manage.py makemigrations --check --dry-run && pytest`
- Frontend build: `cd frontend && npm run typecheck && npm run build`
- Production readiness: `cd backend && python manage.py check_production_readiness --json --fail-on-degraded`
- Launch gate: `bash scripts/ci/launch_gate.sh`
- Production gate: `bash scripts/ci/production_gate.sh`
- Demo seed: `bash scripts/deploy/migrate.sh && python scripts/bootstrap/seed_demo.py`

## Production Environment Checklist

- `DATABASE_URL` points to the production database.
- `DJANGO_SECRET_KEY` is production-only.
- `ALLOWED_HOSTS` includes production domains.
- CORS and CSRF trusted origins match production frontend domains.
- Payment webhook secrets and provider endpoints are configured.
- Media/video object storage credentials are configured.
- Notification providers are configured.
- Background workers and schedulers are deployed.
- Health checks, alerts and logs are connected to production monitoring.
- Database backup and restore procedure has been tested.

## Known Limitations

- Local backend test execution requires the full Django/DRF dependency set in the active interpreter.
- Payment provider live credentials and webhook delivery must be validated in staging.
- Signed video URL delivery and anti-leeching must be validated against production CDN/storage.
- Terms, privacy and refund policy text must be approved before real purchases.

## Release Notes

- v70-v77: payout integrity, repair, audit UI, exports and ops dashboard.
- v80-v85: payment webhooks, idempotency, entitlements, refunds and reconciliation.
- v86-v91: payment admin, customer billing, trainer sales, subscriptions, access guard and notifications.
- v92-v95: CRM, booking, attendance and production readiness.
- v97-v105: content builder, access runtime, video delivery, learning, progress, homework, reviews and messaging.
- v106-v118: docs sync, permissions, tenant isolation, support console, chargebacks, finance/legal/observability/runbooks, CI/CD gate, demo seed and public marketplace hardening.

## Release Decision

Ship condition: CI green, production readiness ok, staging webhook/video/legal validation complete.

Next step: v120 Production Launch Pack.
