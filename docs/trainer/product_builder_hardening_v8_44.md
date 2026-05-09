# v8.44 — Trainer product / bundle builder hardening

## Scope

Adds a trainer-owned product builder on top of the existing `Product` and `ProductItem` tables. No migrations are required.

## Endpoints

```http
GET    /api/v1/products/trainer/
POST   /api/v1/products/trainer/
GET    /api/v1/products/trainer/{id}/
PUT    /api/v1/products/trainer/{id}/
PATCH  /api/v1/products/trainer/{id}/
DELETE /api/v1/products/trainer/{id}/
GET    /api/v1/products/trainer/{id}/readiness/
POST   /api/v1/products/trainer/{id}/publish/
POST   /api/v1/products/trainer/{id}/archive/
```

## Policy

Supported values:

- `product_type`: `video`, `bundle`
- `access_type`: `one_time`, `subscription`
- `status`: `draft`, `published`, `archived`
- `currency`: `RUB`, `USD`, `EUR`

Publishing rules:

- single video product requires exactly one ready trainer-owned video;
- bundle product requires at least two ready trainer-owned videos;
- trainer cannot attach another trainer's videos;
- duplicate video ids are rejected;
- published products must be archived before deletion.

## Verification

```bash
cd backend
python -m py_compile \
  apps/products/services.py \
  apps/products/api/trainer_serializers.py \
  apps/products/api/trainer_views.py \
  apps/products/api/trainer_urls.py \
  config/api.py \
  tests/test_trainer_product_builder.py

python manage.py check
python manage.py makemigrations --check --dry-run
pytest -q tests/test_trainer_product_builder.py
```
