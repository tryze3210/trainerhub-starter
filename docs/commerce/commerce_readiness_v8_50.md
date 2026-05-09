# v8.50 — Commerce readiness checkpoint

This checkpoint closes the v8.41-v8.49 trainer commerce block with a read-only readiness surface.

## API

```http
GET /api/v1/ops/admin/commerce-readiness/
GET /api/v1/ops/admin/commerce-readiness/?include_commands=false&include_frontend=false&include_recommendations=false
```

The endpoint checks that the commercial surface is wired:

- trainer revenue dashboard endpoints from v8.41;
- trainer payout request flow from v8.42;
- trainer content analytics from v8.43;
- trainer product/bundle builder from v8.44;
- checkout integrity from v8.45;
- subscription lifecycle from v8.46;
- entitlement access audit from v8.47;
- trainer onboarding production flow from v8.48;
- public storefront frontend routes from v8.49;
- v8.50 management command and smoke suite.

## Management command

```bash
python manage.py check_commerce_readiness --json
python manage.py check_commerce_readiness --json --fail-on-degraded
```

## Smoke

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
pytest -q tests/test_ops_admin_commerce_readiness.py
pytest -q tests/test_trainer_revenue_dashboard.py tests/test_trainer_payout_request_flow.py tests/test_trainer_content_analytics.py tests/test_trainer_product_builder.py tests/test_checkout_order_integrity.py tests/test_subscription_lifecycle_hardening.py tests/test_entitlement_access_control_audit.py tests/test_trainer_onboarding_production_flow.py
cd ../frontend && npm run typecheck && npm run build && npm run test:contracts
```
