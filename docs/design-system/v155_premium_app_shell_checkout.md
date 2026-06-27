# v155 — Premium App Shell, Footer Cleanup and Checkout Page

## Scope

v155 aligns the global public frame with the premium storefront work and closes the primary purchase path:

- homepage to catalog;
- catalog to product detail;
- product detail to checkout;
- checkout to success or cancel.

## Frontend Shell

- `frontend/src/app/layout.tsx` now uses `app-shell`, `premium-site-header`, `premium-main` and `premium-site-footer`.
- `premium-main` does not wrap all pages in a global container, so premium pages can control their own composition.
- `frontend/src/components/session-nav.tsx` now renders compact role-aware navigation:
  - public: catalog and trainers;
  - student: catalog, learning and messages;
  - trainer: trainer dashboard, students entry point and sales;
  - admin: admin, operations and finance.

## Checkout

New checkout route and components:

- `frontend/src/app/checkout/page.tsx`
- `frontend/src/modules/checkout/components/checkout-page.tsx`
- `frontend/src/modules/checkout/components/checkout-order-summary.tsx`
- `frontend/src/modules/checkout/components/checkout-payment-method.tsx`
- `frontend/src/modules/checkout/components/checkout-trust-panel.tsx`
- `frontend/src/modules/checkout/components/checkout-state-card.tsx`

The checkout page reads product details from search params, uses a stable client idempotency key for the purchase attempt and calls `checkoutApi.checkoutOneTime`.

## Success and Cancel States

- `/checkout/success` now uses Russian premium copy and clear access/order/payment actions.
- `/checkout/cancel` now uses Russian premium copy and recovery actions.

## Styling

`frontend/src/app/globals.css` adds premium shell, footer and checkout classes with dark translucent surfaces, restrained borders, sticky checkout panel and responsive mobile behavior.
