# v8.46 — Subscription lifecycle hardening

## Цель

Закрыть production-слой подписок без миграций: lifecycle policy, renewal projection, cancel/resume hardening, entitlement sync и admin reconciliation.

## Почему без миграций

В текущей модели уже есть persisted statuses:

- `pending`
- `active`
- `past_due`
- `cancelled`
- `expired`

`trialing` и `paused` пока отражены как virtual statuses в policy endpoint. Их нужно вводить отдельной миграцией, когда checkout/subscription provider workflow будет зафиксирован.

## Новые/усиленные endpoints

```http
GET  /api/v1/subscriptions/lifecycle-policy/
GET  /api/v1/subscriptions/lifecycle-summary/?days=30
GET  /api/v1/subscriptions/{id}/renewal-projection/
POST /api/v1/subscriptions/{id}/resume/
POST /api/v1/subscriptions/{id}/sync-entitlements/

GET  /api/v1/subscriptions/admin/lifecycle-policy/
GET  /api/v1/subscriptions/admin/lifecycle-summary/?days=30
POST /api/v1/subscriptions/{id}/admin/sync-entitlements/
POST /api/v1/subscriptions/admin/reconcile-entitlements/
```

Existing endpoints remain compatible:

```http
GET  /api/v1/subscriptions/center/
POST /api/v1/subscriptions/{id}/cancel/
POST /api/v1/subscriptions/{id}/reactivate/
GET  /api/v1/subscriptions/admin/overview/
POST /api/v1/subscriptions/{id}/admin/mark-past-due/
POST /api/v1/subscriptions/admin/expire-due/
```

## Entitlement policy

- `active` and unexpired `past_due` subscriptions should have active library entitlement.
- `cancelled` and `expired` subscriptions should not have active subscription entitlements.
- sync is idempotent and writes audit/domain events.

## Management command

```bash
python manage.py sync_subscription_entitlements --json
python manage.py sync_subscription_entitlements --subscription-id <uuid> --json
```

## Проверка

```bash
cd backend
python -m py_compile \
  apps/subscriptions/lifecycle.py \
  apps/subscriptions/api/lifecycle_serializers.py \
  apps/subscriptions/api/serializers.py \
  apps/subscriptions/api/views.py \
  apps/subscriptions/management/commands/sync_subscription_entitlements.py \
  tests/test_subscription_lifecycle_hardening.py

python manage.py check
python manage.py makemigrations --check --dry-run
pytest -q tests/test_subscription_lifecycle_hardening.py
pytest -q tests/contracts/test_api_surface.py
pytest -q
```

Frontend:

```bash
cd frontend
npm run typecheck
npm run build
npm run test:contracts
```
