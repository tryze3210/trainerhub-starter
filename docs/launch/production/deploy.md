# Production Deploy

## Preflight

- Confirm `VERSION` is `v120-production-launch-pack`.
- Run `bash scripts/ci/production_gate.sh`.
- Confirm `python manage.py check_production_readiness --json --fail-on-degraded` exits cleanly.
- Confirm migrations are reviewed and reversible where practical.
- Confirm staging webhook, video and legal-document validation is complete.

## Deploy

1. Build backend and frontend artifacts from the release commit.
2. Apply database migrations.
3. Deploy backend web process.
4. Deploy background workers and schedulers.
5. Deploy frontend build.
6. Warm health/readiness endpoints.
7. Run a production smoke pass without mutating real customer data.

## Post-deploy Checks

- Runtime health endpoints respond.
- Payment webhook endpoint accepts signed staging/live validation events.
- Admin production readiness is `ok`.
- Observability runtime has no critical alerts.
- Rollback commit and database restore point are known.
