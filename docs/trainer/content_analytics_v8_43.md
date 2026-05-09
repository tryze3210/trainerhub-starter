# v8.43 — Trainer content performance analytics

## Goal

Give trainers a commercial analytics screen for their own content without exposing admin-only marketplace analytics.

## Backend endpoints

```http
GET /api/v1/trainers/me/analytics/overview/?days=30
GET /api/v1/trainers/me/analytics/content/?type=all&days=30&limit=50
GET /api/v1/trainers/me/analytics/sales/?days=30&limit=50
```

All endpoints require an authenticated trainer (`IsTrainer`).

## Data sources

- `Video` and `Product` owned by the trainer.
- `ProductItem` for product/video relationships.
- `OrderItem` for matched sales by UUID/slug.
- `BalanceEntry` from the trainer wallet for revenue attribution.
- `MediaAsset.metadata_json.views_count` for video views when available.

## No migrations

The feature is read-only and uses existing tables.

## Frontend

New page:

```text
/trainer/dashboard/analytics
```

It shows:

- net/gross revenue;
- views;
- purchases;
- video/product counts;
- top content table;
- recent sales table;
- period and content type filters.

## Smoke checks

```bash
cd backend
python manage.py check
pytest -q tests/test_trainer_content_analytics.py
pytest -q tests/test_trainer_revenue_dashboard.py

cd ../frontend
npm run typecheck
npm run build
npm run test:contracts
```
