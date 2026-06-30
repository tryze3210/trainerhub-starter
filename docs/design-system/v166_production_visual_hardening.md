# v166 / v166.1 — Production Visual Hardening Pass

## Scope

v166 is a production visual hardening pass, not a feature release. It keeps backend and API behavior unchanged and only tightens UI/CSS/copy/className contracts for the commercial demo surface.

The pass covers overflow safety, readable empty/loading/error states, responsive consistency, CTA wrapping, long-string handling and removal of primary raw technical labels where the premium UI already has human labels.

## Why v166.1 Was Needed

v166 created the production visual hardening roadmap and route QA matrix, but the CSS and contract-test layer needed to be locked. v166.1 adds the scoped CSS hardening rules to globals.css, restores/protects the v165.3 trainer dashboard/video studio hooks, and adds contract tests for README, documentation, CSS selectors, responsive breakpoints and long-string safety rules.

## Updated Areas

- Public storefront
- Product detail pages
- Checkout
- Customer cabinet
- Learning area
- Trainer dashboard and trainer routes
- Video/content studio
- Admin operations dashboards
- Global app shell

## Visual QA Rules

1. No horizontal page overflow.
2. No nested vertical scroll inside cards/panels unless intentionally documented.
3. No text overlap.
4. Long titles, URLs, slugs and IDs wrap safely.
5. Mobile layouts collapse to one column where needed.
6. CTA buttons wrap and keep consistent height.
7. Loading/error/empty states are styled and human-readable.
8. Russian user-facing labels for the commercial UI zones already localized.
9. Raw UUID/status/type/source fields are not primary UI text.
10. Tables are only used where data density requires them; otherwise cards/timeline/rails.

## CSS Safety Rules

- Scoped additions only inside known premium, customer, trainer, admin, checkout, marketplace, product and learning shells.
- No global reset.
- No Tailwind.
- No UI libraries.
- `min-width: 0` for flex/grid children.
- `overflow-wrap: anywhere` for long strings, URLs, slugs, file names, emails and IDs.
- Line-clamp where titles and descriptions can become too long.
- Responsive breakpoints: 1180px, 1024px, 768px, 640px.
- Safe horizontal rails use `overflow-x: auto`, `overflow-y: hidden`, `scroll-snap-type: x mandatory` and local scroll only.
- v166.1 confirms the rules exist in `frontend/src/app/globals.css`.
- v166.1 preserves v165.3 trainer hooks:
  - `.trainer-home-workbench`
  - `.trainer-video-studio-workbench`
  - `.trainer-content-upload-dropzone`
  - `.trainer-content-card--active`

## Route QA Matrix

Public:

- `/` — storefront hero, CTA rows, premium sections and app shell checked for page overflow, safe wrapping and responsive collapse.
- `/catalog` — catalog filters, marketplace cards and product grids checked for mobile wrap and long-title safety.
- `/catalog/videos/[slug]` — product detail hero, purchase panel and content sections checked for safe long slugs/titles and no overlap.
- `/catalog/programs/[slug]` — product detail layout and purchase panel checked for responsive one-column collapse.
- `/catalog/bundles/[slug]` — bundle detail layout checked for CTA wrapping and safe horizontal rails.
- `/checkout` — checkout layout, payment cards and order summary checked for right-side overflow and wrapped actions.
- `/checkout/success` — premium success state checked for readable human copy and safe CTA layout.
- `/checkout/cancel` — premium cancel/error state checked for readable human copy and safe CTA layout.

Customer:

- `/customer/hub` — cabinet cards, metrics, library, orders, subscriptions, recommendations, favorites and reviews checked for readable mobile cards and localized empty states.
- `/customer/orders` — customer order surfaces covered by customer scoped safety rules where present.
- `/customer/billing` — billing/invoice surfaces covered by customer scoped safety rules where present.
- `/customer/subscriptions` — subscription cards covered by customer scoped safety rules where present.
- `/customer/reviews` — review opportunities covered by customer scoped safety rules where present.
- `/customer/favorites` — favorites cards covered by customer scoped safety rules where present.
- `/learning` — lesson/player area, lesson list, locked/access states and material cards checked for no double vertical scroll and human-readable states.

Trainer:

- `/trainer/dashboard` — trainer cockpit, KPI grid, timeline, product rail and side panels checked for v165.3 CSS contract preservation and v166 overflow safety.
- `/trainer/business` — business cockpit cards, risks, payout summaries and local panels checked for wrapping and no nested vertical scroll.
- `/trainer/dashboard/products` — product builder, media picker, selected media list and advanced ID field checked for horizontal workbench safety.
- `/trainer/videos` — video/content studio checked for upload dropzone, card actions, tabs, rails and v165.3 hook preservation.
- `/trainer/dashboard/crm` — CRM cards, customer names and filters checked for safe wrapping.
- `/trainer/dashboard/assignments` — assignment/review cards and action rows checked for safe wrap and localized states.
- `/trainer/dashboard/schedule` — booking/calendar surfaces checked for horizontal table/rail safety.
- `/trainer/dashboard/sales` — sales dashboard cards and rows checked for long product/customer strings.
- `/trainer/dashboard/revenue` — revenue dashboards checked for card/grid shrink and chart container safety.
- `/trainer/dashboard/payouts` — payout request cards checked for long account/status strings and no card scrollbars.
- `/trainer/dashboard/analytics` — analytics panels checked for chart/container shrink.
- `/trainer/reviews` — review workbench cards and reply actions checked for wrap.
- `/trainer/onboarding` — onboarding form, status cards and action rows checked for mobile one-column collapse.
- `/trainer/application-status` — application status timeline and actions checked for readable wrapping.

Admin/Ops:

- `/admin` — admin cockpit cards and app shell checked for safe wrapping.
- `/admin/payments` — payment operation dashboard tables, filters and long payment IDs covered by table wrapper and long-string CSS.
- `/admin/payouts` — payout tables/detail links and long payout IDs covered by table wrapper and long-string CSS.
- `/admin/moderation` — moderation tables/cards covered by admin scoped safety rules.
- `/admin/operations` — ops dashboard cards and health indicators covered by admin scoped safety rules.
- `/admin/support` — support routes covered by admin/support scoped safety rules where present.
- `/admin/reconciliation` — reconciliation tables covered by local horizontal table scrolling only.
- `/admin/reviews` — review moderation tables/cards covered by admin scoped safety rules.
- `/admin/trainers/applications` — trainer application review cards/tables covered by admin scoped safety rules.

## Backend/API Scope

Backend unchanged.
API unchanged.
Only UI/CSS/copy/className/contract tests.

## Verification

```bash
cd frontend
npm run typecheck
npm run test:contracts
npm run build
git diff --check
```

## Known Limitation

Build may fail because of the existing `.next/trace` ownership/cache issue. If the failure is exactly that, show the exact error and do not report build passed.
