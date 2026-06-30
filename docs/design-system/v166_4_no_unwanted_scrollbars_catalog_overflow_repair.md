# v166.4 — No Unwanted Scrollbars, Catalog Overflow Repair and UI Noise Cleanup

## Scope

v166.4 is an anti-scroll and overflow repair pass. It does not add new product functionality and does not change backend, API contracts or business logic.

The pass focuses on visible UI quality after the production visual hardening block, with special attention to `/catalog`.

## Main Problem

The user noticed an unwanted scrollbar in the public catalog. These issues usually come from `min-width`, `white-space: nowrap`, fixed widths, table wrappers, horizontal rails, action rows, filter chips, long titles, slugs, URLs or file names.

## Updated Areas

- Public catalog
- Marketplace cards
- Product detail pages
- App shell/header/footer
- Checkout
- Customer cabinet
- Learning area
- Trainer workspace
- Admin/ops dashboards

## Scrollbar Policy

1. The page should have only the main document vertical scroll.
2. Cards, panels, hero sections, sidebars and forms should not use `overflow-y: auto` or `overflow-y: scroll`.
3. Horizontal scroll is allowed only for explicitly scoped rails or table wrappers.
4. Filter chips must not create visible right-side page overflow.
5. On mobile, major layouts collapse to one column.
6. CTA and action rows wrap instead of expanding the page.
7. Long titles, slugs, URLs and file names wrap safely.
8. Tables may scroll horizontally only inside a table wrapper, never on the whole page.

## Catalog QA

- `/catalog` desktop 1440px: no right horizontal page scroll.
- `/catalog` laptop 1280px: no nested vertical scrollbars.
- `/catalog` tablet 768px: filters stay inside their row and use only local horizontal scroll when needed.
- `/catalog` mobile 390px: cards stay inside a one-column grid.
- Filter chips do not create a second page scrollbar.
- Cards do not escape the grid.
- Featured product does not force page width.
- CTA buttons wrap safely.
- Skeleton, loading, error and empty states do not create overflow.

## Route QA Matrix

Public:

- `/`
- `/catalog`
- `/catalog/videos/[slug]`
- `/catalog/programs/[slug]`
- `/catalog/bundles/[slug]`
- `/trainers`

Checkout:

- `/checkout`
- `/checkout/success`
- `/checkout/cancel`

Customer:

- `/customer/hub`
- `/customer/orders`
- `/customer/billing`
- `/customer/subscriptions`
- `/customer/reviews`
- `/customer/favorites`
- `/learning`

Trainer:

- `/trainer/dashboard`
- `/trainer/business`
- `/trainer/dashboard/products`
- `/trainer/videos`
- `/trainer/dashboard/crm`
- `/trainer/dashboard/assignments`
- `/trainer/dashboard/schedule`
- `/trainer/dashboard/sales`
- `/trainer/dashboard/revenue`
- `/trainer/dashboard/payouts`
- `/trainer/dashboard/analytics`
- `/trainer/reviews`
- `/trainer/onboarding`
- `/trainer/application-status`

Admin/Ops:

- `/admin`
- Existing admin payment, payout, moderation and support routes.

## Catalog Repair Notes

- Catalog filters use `.premium-catalog-filter-row` as the only local mobile horizontal rail.
- Catalog cards use `.premium-catalog-grid` with `auto-fit` and `minmax(min(100%, 280px), 1fr)`.
- Marketplace card titles and descriptions are clamped and wrap safely.
- Header, navigation and footer action rows wrap instead of expanding the viewport.

Intentional scroll areas that may remain:

- Explicit horizontal rails.
- Table wrappers.
- Native video player controls and timelines.

## Backend/API Scope

Backend unchanged.
API unchanged.
Only CSS, className, UI copy, contract tests and docs.

## Verification

```bash
cd frontend
npm run typecheck
npm run test:contracts
npm run build
git diff --check
```

## Known Limitation

Build may fail due to the existing `.next/trace` ownership/cache issue. If so, show the exact error and do not claim build passed.
