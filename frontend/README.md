# TrainerHub Frontend

Готовый Next.js frontend под текущий Django/DRF backend.

## Что покрыто
- auth: `register`, `login`, `refresh`, `logout`, `me`
- public content storefront:
  - `/api/v1/content/videos/`
  - `/api/v1/content/programs/`
  - `/api/v1/content/bundles/`
- private cabinet slices:
  - `/api/v1/orders/`
  - `/api/v1/payments/`
  - `/api/v1/subscriptions/`
  - `/api/v1/entitlements/`
- purchase flow:
  - `/api/v1/orders/checkout/`
  - `/api/v1/payments-webhooks/receive/`
