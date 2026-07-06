# v167 API Route Matrix

This matrix documents the frontend-facing backend routes covered by the v167 production foundation contract. The executable source of truth is `backend/tests/test_api_route_matrix_v167.py`.

## Covered Areas

| Area | Example route | URL name |
| --- | --- | --- |
| Auth | `/api/v1/auth/me/` | `auth-me` |
| Public marketplace | `/api/v1/public-catalog/` | `public-marketplace-home` |
| Content catalog | `/api/v1/content/videos/` | `published-videos-list` |
| Trainers | `/api/v1/trainers/me/onboarding/status/` | `trainer-me-onboarding-status` |
| Commerce | `/api/v1/orders/checkout/` | `orders-checkout` |
| Payouts | `/api/v1/payouts/my/balance/` | `my-payouts-balance` |
| Products | `/api/v1/products/trainer/` | `trainer-products-list` |
| Subscriptions | `/api/v1/subscriptions/lifecycle-policy/` | `subscriptions-lifecycle-policy` |
| Access | `/api/v1/entitlements/me/access-check/` | `entitlements-me-access-check` |
| Ops | `/api/v1/ops/admin/production-readiness/` | `ops-admin-production-readiness` |
| Referrals | `/api/v1/referrals/admin/ops/overview/` | `referrals-admin-ops-overview` |
| Audit | `/api/v1/audit/admin/events/export.csv` | `admin-audit-events-export` |
| Booking | `/api/v1/booking/me/schedule/` | `booking-me-schedule` |
| Messaging | `/api/v1/messaging/me/inbox/` | `messaging-inbox` |
| Notifications | `/api/v1/notifications/inbox/` | `notification-inbox` |

## Contract Rules

- Routes are resolved through the active Django `config.urls` tree.
- Each route must resolve to the expected `url_name`, not merely to any matching dynamic route.
- Dynamic examples use safe placeholders such as `demo-program`, `demo-trainer` or `demo-payout`.
- This contract does not call views or touch the database; it only protects mounted URL surface.

## Verification

```bash
cd backend
.venv/bin/python -m pytest tests/test_api_route_matrix_v167.py -q
```
