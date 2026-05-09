# v8.42.1 — payout request flow non-destructive hotfix

v8.42 accidentally replaced the existing payouts API ViewSet/router files with shorter APIView files. That removed existing admin operations endpoints such as projection health, risk holds, reconciliation and payout outbox projection.

This hotfix restores the ViewSet/router API shape and adds v8.42 direct payout transitions as extra ViewSet actions, without deleting the existing endpoints.

Restored/kept endpoints:

- `GET /api/v1/payouts/my/`
- `GET /api/v1/payouts/my/balance/`
- `POST /api/v1/payouts/my/request/`
- `GET /api/v1/payouts/admin/overview/`
- `POST /api/v1/payouts/admin/{id}/transition/`
- `POST /api/v1/payouts/admin/bulk-transition/`
- `GET /api/v1/payouts/admin/projection-health/`
- `POST /api/v1/payouts/admin/project-outbox/`
- `GET /api/v1/payouts/admin/risk-holds/`
- `GET /api/v1/payouts/admin/risk-holds/summary/`
- `POST /api/v1/payouts/admin/risk-holds/release/`
- `GET /api/v1/payouts/admin/reconciliation/`
- `POST /api/v1/payouts/admin/reconciliation/repair/`

Added direct transition endpoints:

- `POST /api/v1/payouts/admin/{id}/approve/`
- `POST /api/v1/payouts/admin/{id}/processing/`
- `POST /api/v1/payouts/admin/{id}/mark-paid/`
- `POST /api/v1/payouts/admin/{id}/reject/`

No migrations required.
