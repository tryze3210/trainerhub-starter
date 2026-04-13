# v34 install

1. Add `apps.finance_reporting` to `INSTALLED_APPS`.
2. Include `apps.finance_reporting.api.urls` under `/api/v1/finance/`.
3. Run migrations: `python manage.py migrate`.
4. Bootstrap snapshots: `python manage.py rebuild_finance_reporting --days=45`.
5. Wire Celery beat snippet for nightly reconciliation refresh.

## Endpoints
- `GET /api/v1/finance/admin/overview/?days=30`
- `POST /api/v1/finance/admin/refresh/`
- `GET /api/v1/finance/admin/settlements/`
- `POST /api/v1/finance/admin/settlements/build/`
- `POST /api/v1/finance/admin/settlements/<uuid>/finalize/`
- `GET /api/v1/finance/admin/settlements/<uuid>/export/csv/`
- `GET /api/v1/finance/admin/settlements/<uuid>/export/xlsx/`

## Important mapping seam
Adapt app labels and fields only in `backend/apps/finance_reporting/services/reconciliation.py`.
Current assumptions:
- `orders.Order.total_amount`, `orders.Order.status`, `orders.Order.trainer`, `orders.Order.created_at`
- `payments.Payment.amount`, `payments.Payment.status`, `payments.Payment.order`, `payments.Payment.created_at`
- `payments.Payout.amount`, `payments.Payout.status`, `payments.Payout.order`, `payments.Payout.created_at`
