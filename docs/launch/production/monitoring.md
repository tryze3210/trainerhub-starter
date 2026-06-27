# Monitoring

## Required Signals

- Runtime health and readiness.
- Payment webhook failure rate.
- Payment error rate.
- Payout repair rate.
- Background job failures.
- Notification delivery failures.
- Database latency and connection saturation.

## Admin Checks

- `GET /api/v1/ops/admin/observability-runtime/`
- `GET /api/v1/ops/admin/production-readiness/`
- `GET /api/v1/ops/admin/runbooks/`

## Alert Routing

- Payments and webhook alerts route to support plus finance.
- Payout mismatch alerts route to finance.
- Entitlement/access alerts route to support.
- Infrastructure alerts route to engineering/on-call.
