# TrainerHub — current version v165.3

TrainerHub is a trainer commerce platform with admin operations, customer billing, trainer sales, payout controls, subscriptions, entitlements, audit trails, notifications, CRM, booking, attendance, and production-readiness checks.

This README describes the current roadmap state after v165.3 Trainer Dashboard and Video Studio CSS Contract Lock. The v70-v95 platform-readiness block, v97-v105 content-learning launch block, v106-v120 production-launch block and v131-v150 UX redesign block are closed; the v151-v165.3 premium storefront, customer workspace and trainer workspace block is now implemented.

v163 завершил premium polish для заданий, отзывов и заявок на выплаты тренера.

v164 завершил trainer business cockpit, onboarding application и application status polish.

v165 синхронизирует главный cockpit тренера, video/content studio и route-level QA.

v165.1 closes the unfinished v165 sync: README versioning, trainer dashboard cockpit, video studio route shell, upload/card polish and route-level QA documentation are aligned.

v165.2 closes the unfinished v165/v165.1 polish by aligning README versioning, route-level video shell, dashboard/studio scoped CSS contracts, upload cards and route QA documentation.

v165.3 locks the v165 dashboard/video studio polish by adding the missing scoped CSS layer and contract tests for trainer-home, trainer-video-studio and trainer-content class hooks.

## Current Roadmap State

Roadmap status table:

| Version | Area | Status |
| --- | --- | --- |
| v70-v77 | Payout integrity, repair, exports, ops dashboard | Done |
| v80-v85 | Payments, orders, entitlements, refunds, reconciliation | Done |
| v86-v91 | Payment admin UI, customer billing, trainer sales, subscriptions, access guard, notifications | Done |
| v92-v95 | CRM, booking, attendance, production readiness | Done |
| v96 | Docs/version cleanup | Done |
| v97 | Course / Program Builder | Done |
| v98 | Content Access Runtime | Done |
| v99 | Video Delivery Hardening | Done |
| v100 | Student Learning Area | Done |
| v101 | Progress Tracking | Done |
| v102 | Assignments / Homework | Done |
| v103 | Reviews / Feedback Loop | Done |
| v104 | Messaging Core | Done |
| v105 | Launch Hardening | Done |
| v106 | Documentation Final Sync | Done |
| v107 | Role Matrix / Permission Audit | Done |
| v108 | Tenant Isolation Hardening | Done |
| v109 | Admin Global Search | Done |
| v110 | Support Console | Done |
| v111 | Disputes / Chargebacks | Done |
| v112 | Finance Documents | Done |
| v113 | Tax / Legal Compliance | Done |
| v114 | Observability Runtime | Done |
| v115 | Ops Runbooks | Done |
| v116 | CI/CD Production Gate | Done |
| v117 | Demo Data / Seed Scenarios | Done |
| v118 | Public Marketplace Hardening | Done |
| v119 | Launch Candidate | Done |
| v120 | Production Launch Pack | Done |
| v131 | UI Design System | Done |
| v132 | Layout System | Done |
| v133 | Component Library | Done |
| v134 | Theme Engine | Done |
| v135 | Motion / UI Polish | Done |
| v136 | Admin Dashboard | Done |
| v137 | Trainer Workspace | Done |
| v138 | CRM | Done |
| v139 | Booking | Done |
| v140 | Payments | Done |
| v141 | Payouts | Done |
| v142 | Student Portal | Done |
| v143 | Learning Experience | Done |
| v144 | Public Marketplace | Done |
| v145 | Mobile Responsive Pass | Done |
| v146 | Premium Charts | Done |
| v147 | Drag And Drop Kanban | Done |
| v148 | Realtime Notifications UI | Done |
| v149 | Command Palette / Fast Search | Done |
| v150 | Premium UX Completion | Done |
| v151 | Premium Brand Foundation | Done |
| v152 | Premium Marketing Home Page | Done |
| v153 | Premium Storefront Stabilization | Done |
| v154-prep | Marketplace Catalog Premium Foundation | Done |
| v154 | Premium Product Detail Landing Pages | Done |
| v155 | Premium App Shell, Footer Cleanup and Checkout Page | Done |
| v156 | Premium Customer Cabinet and All Customer Sections | Done |
| v157 | Premium Trainer Cabinet Shell and Core Trainer Sections | Done |
| v157.1 | Trainer Cabinet Integration Repair | Done |
| v158 | Premium Trainer Product Builder | Done |
| v158.1 | Final Product Builder and Video Studio Repair | Done |
| v158.2 | Product/Video Studio Usability Repair | Done |
| v158.3 | Horizontal Workbench Rescue | Done |
| v159 | Premium Profile Workbench System | Done |
| v159.1 | Premium Profile Background and Surface Repair | Done |
| v159.2 | Remove Nested Scrollbars and Polish Profile Workbench | Done |
| v160 | Premium Media Library Picker and Product Publishing Flow | Done |
| v160.1 | Integrate Media Picker Into Product Builder | Done |
| v160.2 | Product/Video Flow Stabilization Before CRM | Done |
| v160.3 | Product Media Picker Cleanup and CSS Layer Stabilization | Done |
| v160.4 | Product Media Single Source of Truth | Done |
| v161 | Premium Trainer CRM and Schedule Pages | Done |
| v162 | Premium Trainer Finance & Analytics Workbenches | Done |
| v163 | Premium Trainer Education, Reviews and Payout Request Workbenches | Done |
| v164 | Premium Trainer Business, Onboarding and Application Status Workbenches | Done |
| v165 | Premium Trainer Dashboard, Video Studio and Route QA Pass | Done |
| v165.1 | Finalize Premium Trainer Dashboard, Video Studio and Route QA Sync | Done |
| v165.2 | CSS Contract, README Sync and Trainer Studio Finalization | Done |
| v165.3 | Trainer Dashboard and Video Studio CSS Contract Lock | Current |

Completed implementation line:

- v70 — Integrity Snapshot
- v72 — Repair Preview
- v73 — Repair Execution
- v74 — Payout Repair Audit UI
- v75 — Reconciliation Report Export
- v76 — Repair Audit Export
- v77 — Ops Dashboard Hardening
- v80 — Payment Webhook Hardening
- v81 — Payment Idempotency
- v82 — Entitlement Activation
- v83 — Refund Flow
- v84 — Revoke Entitlement
- v85 — Payment Reconciliation
- v86 — Payment Admin UI
- v87 — Customer Billing UI
- v88 — Trainer Sales Dashboard
- v89 — Subscription Lifecycle
- v90 — Access Guard Hardening
- v91 — Notification System
- v92 — CRM Core
- v93 — Booking / Schedule
- v94 — Attendance / Check-in
- v95 — Production Readiness Pass
- v96 — Docs/version cleanup
- v97 — Course / Program Builder
- v98 — Content Access Runtime
- v99 — Video Delivery Hardening
- v100 — Student Learning Area
- v101 — Progress Tracking
- v102 — Assignments / Homework
- v103 — Reviews / Feedback Loop
- v104 — Messaging Core
- v105 — Launch Hardening
- v106 — Documentation Final Sync
- v107 — Role Matrix / Permission Audit
- v108 — Tenant Isolation Hardening
- v109 — Admin Global Search
- v110 — Support Console
- v111 — Disputes / Chargebacks
- v112 — Finance Documents
- v113 — Tax / Legal Compliance
- v114 — Observability Runtime
- v115 — Ops Runbooks
- v116 — CI/CD Production Gate
- v117 — Demo Data / Seed Scenarios
- v118 — Public Marketplace Hardening
- v119 — Launch Candidate
- v120 — Production Launch Pack
- v131 — UI Design System
- v132 — Layout System
- v133 — Component Library
- v134 — Theme Engine
- v135 — Motion / UI Polish
- v136 — Admin Dashboard
- v137 — Trainer Workspace
- v138 — CRM
- v139 — Booking
- v140 — Payments
- v141 — Payouts
- v142 — Student Portal
- v143 — Learning Experience
- v144 — Public Marketplace
- v145 — Mobile Responsive Pass
- v146 — Premium Charts
- v147 — Drag And Drop Kanban
- v148 — Realtime Notifications UI
- v149 — Command Palette / Fast Search
- v150 — Premium UX Completion
- v151 — Premium Brand Foundation
- v152 — Premium Marketing Home Page
- v153 — Premium Storefront Stabilization
- v154-prep — Marketplace Catalog Premium Foundation
- v154 — Premium Product Detail Landing Pages
- v155 — Premium App Shell, Footer Cleanup and Checkout Page
- v156 — Premium Customer Cabinet and All Customer Sections
- v157 — Premium Trainer Cabinet Shell and Core Trainer Sections
- v157.1 — Trainer Cabinet Integration Repair
- v158 — Premium Trainer Product Builder
- v158.1 — Final Product Builder and Video Studio Repair
- v158.2 — Product/Video Studio Usability Repair
- v158.3 — Horizontal Workbench Rescue
- v159 — Premium Profile Workbench System
- v159.1 — Premium Profile Background and Surface Repair
- v159.2 — Remove Nested Scrollbars and Polish Profile Workbench
- v160 — Premium Media Library Picker and Product Publishing Flow
- v160.1 — Integrate Media Picker Into Product Builder
- v160.2 — Product/Video Flow Stabilization Before CRM
- v160.3 — Product Media Picker Cleanup and CSS Layer Stabilization
- v160.4 — Product Media Single Source of Truth
- v161 — Premium Trainer CRM and Schedule Pages
- v162 — Premium Trainer Finance & Analytics Workbenches
- v163 — Premium Trainer Education, Reviews and Payout Request Workbenches
- v164 — Premium Trainer Business, Onboarding and Application Status Workbenches
- v165 — Premium Trainer Dashboard, Video Studio and Route QA Pass
- v165.1 — Finalize Premium Trainer Dashboard, Video Studio and Route QA Sync
- v165.2 — CSS Contract, README Sync and Trainer Studio Finalization
- v165.3 — Trainer Dashboard and Video Studio CSS Contract Lock

The v70-v95 production-readiness roadmap is now closed at the platform gate level.
The v97-v105 content-learning launch roadmap is now closed at the launch gate level.

## UI Design System

v131 starts the UX redesign block with a shared frontend foundation.

Design-system files:

- `frontend/src/design-system/tokens.ts`
- `frontend/src/design-system/components.tsx`
- `frontend/src/design-system/index.ts`
- `docs/design-system/v131_ui_design_system.md`
- `frontend/tests/contracts/design-system-contract.test.js`

Covered primitives:

- colors, typography, spacing and radius tokens;
- buttons, forms, tables, cards and badges;
- modal shell;
- skeleton loader and focus ring;
- statistics card primitive.

## Layout System

v132 adds shared page layout primitives for the redesign block.

Layout files:

- `frontend/src/design-system/layouts.tsx`
- `docs/design-system/v132_layout_system.md`

Covered layouts:

- Admin Layout;
- Trainer Layout;
- Student Layout;
- Public Layout;
- Mobile Layout through responsive sidebar behavior and sticky mobile action bar.

## Component Library

v133 adds shared presentational components for the upcoming screen redesign pass.

Component library files:

- `frontend/src/design-system/library.tsx`
- `docs/design-system/v133_component_library.md`

Covered components:

- DataTable and statistics cards;
- compact bar charts;
- booking/schedule calendar;
- CRM/support Kanban board;
- file upload shell;
- rich text editor shell;
- protected-content video player shell.

## Theme Engine

v134 adds runtime theme support for the redesign block.

Theme files:

- `frontend/src/design-system/theme.tsx`
- `docs/design-system/v134_theme_engine.md`

Covered theme features:

- light and dark modes;
- brand palettes for `trainerhub`, `studio`, `academy` and `wellness`;
- white-label CSS variable overrides;
- `DSThemeProvider`, `useDSTheme` and `getWhiteLabelThemeStyle`.

## Motion / UI Polish

v135 closes the first UX foundation block with shared feedback states and reduced-motion support.

Motion and feedback files:

- `frontend/src/design-system/feedback.tsx`
- `docs/design-system/v135_motion_ui_polish.md`

Covered feedback primitives:

- skeleton stacks;
- empty states;
- toast and toast stack;
- transition panel;
- status dot;
- reduced-motion CSS guard.

## Admin Dashboard

v136 starts the screen redesign pass by moving `/admin` onto shared design-system primitives.

Updated admin screen:

- `frontend/src/app/admin/page.tsx`

Covered UI changes:

- design-system page header;
- shared statistics grid;
- moderation, payout and review sections;
- payout status chart;
- skeleton loading state;
- empty states and status dots.

## Trainer Workspace

v137 moves the trainer workspace shell and main dashboard onto shared design-system primitives.

Updated trainer files:

- `frontend/src/modules/trainer-dashboard/components/trainer-dashboard-shell.tsx`
- `frontend/src/app/trainer/dashboard/page.tsx`

Covered UI changes:

- trainer layout and side navigation primitives;
- design-system page header;
- KPI statistics grids;
- trainer profile and CMS sections;
- revenue chart;
- skeleton loading state;
- empty states and status dots.

## CRM Redesign

v138 moves the trainer CRM dashboard onto shared design-system primitives.

Updated CRM file:

- `frontend/src/modules/trainer-crm/components/trainer-crm-dashboard.tsx`

Covered UI changes:

- CRM controls through shared form primitives;
- customer list through shared DataTable;
- summary statistics grid;
- customer detail sections;
- rich text editor shell for trainer notes;
- empty states, skeleton loading and status dots.

## Booking Redesign

v139 moves the trainer booking/schedule dashboard onto shared design-system primitives.

Updated booking file:

- `frontend/src/modules/trainer-booking/components/trainer-booking-dashboard.tsx`

Covered UI changes:

- schedule controls through shared form primitives;
- booking KPIs through shared statistics grids;
- schedule calendar preview;
- availability, generation, reservations and waitlist sections;
- slots and attendance through shared DataTable;
- empty states and skeleton loading.

## Payments Redesign

v140 moves the admin payment operations dashboard onto shared design-system primitives.

Updated payments file:

- `frontend/src/modules/admin-payments/components/admin-payment-operations-dashboard.tsx`

Covered UI changes:

- payment, webhook and refund tables through shared DataTable;
- payment operations KPIs through shared statistics grid;
- payment/webhook filters through shared form primitives;
- reconciliation, status buckets, refunds and webhook sections;
- empty states, skeleton loading and status dots.

## Payouts Redesign

v141 moves the admin payout operations dashboard shell onto shared design-system primitives while preserving payout state-machine actions.

Updated payouts file:

- `frontend/src/modules/admin-payouts/components/admin-payout-operations-dashboard.tsx`

Covered UI changes:

- payout operation sections through shared section/card primitives;
- payout KPI cards through shared statistics cards;
- health indicators through shared status dots;
- loading state through shared skeleton;
- admin-role warning through shared card primitive.

## Student Portal Redesign

v142 moves the customer/student marketplace hub onto shared design-system primitives.

Updated student portal file:

- `frontend/src/app/customer/hub/page.tsx`

Covered UI changes:

- page header through shared header primitive;
- student/customer KPIs through shared statistics grid;
- library, orders, subscriptions, reviews, favorites and recommendations through shared sections;
- loading through shared skeleton;
- empty states and readiness status dots.

## Learning Experience Redesign

v143 moves the student learning area onto shared design-system primitives.

Updated learning file:

- `frontend/src/app/learning/page.tsx`

Covered UI changes:

- learning page header through shared header primitive;
- learning summary through shared statistics grid;
- next lesson, runtime lesson, course/program, lesson and materials areas through shared sections;
- loading through shared skeleton;
- empty states and lesson access status dots.

## Public Marketplace Redesign

v144 moves the public marketplace catalog onto shared design-system primitives.

Updated marketplace file:

- `frontend/src/modules/public-storefront/components/marketplace-catalog-page.tsx`

Covered UI changes:

- catalog page header through shared header primitive;
- catalog filters through shared form primitives;
- featured/catalog areas through shared sections;
- loading through shared skeleton;
- empty state for no-results;
- catalog item badges through shared badge primitive.

## Mobile Responsive Pass

v145 closes the screen redesign block by hardening mobile behavior across shared UI primitives.

Updated mobile layer:

- `frontend/src/app/globals.css`
- `frontend/tests/contracts/design-system-contract.test.js`

Covered responsive behavior:

- horizontal overflow guard;
- mobile page headers and action wrapping;
- responsive layout navigation;
- compact mobile cards and buttons;
- calendar and Kanban mobile scrolling;
- modal, toast, upload and rich-text mobile handling;
- contract checks for mobile CSS rules.

## Premium Charts

v146 starts the premium UX block by adding richer shared chart primitives without introducing a new chart dependency.

Updated chart layer:

- `frontend/src/design-system/library.tsx`
- `frontend/src/app/globals.css`
- `frontend/tests/contracts/design-system-contract.test.js`
- `docs/design-system/v146_premium_charts.md`

Covered components:

- `DSPremiumLineChart` for trend views;
- `DSDonutChart` for distribution views;
- `DSInsightChartCard` for metric/chart compositions;
- responsive chart CSS for mobile dashboards;
- contract checks for premium chart exports and CSS classes.

## Drag And Drop Kanban

v147 adds native drag-and-drop behavior to the shared Kanban primitive while keeping persistence and ordering decisions in feature modules.

Updated Kanban layer:

- `frontend/src/design-system/library.tsx`
- `frontend/src/app/globals.css`
- `frontend/tests/contracts/design-system-contract.test.js`
- `docs/design-system/v147_drag_drop_kanban.md`

Covered behavior:

- `DSKanbanBoard` accepts `onCardMove`;
- move payload includes `cardId`, `fromColumnId` and `toColumnId`;
- cards become draggable only when a move handler exists;
- columns become drop targets only for interactive boards;
- contract checks for drag/drop API and visual states.

## Realtime Notifications UI

v148 adds shared UI primitives for realtime connection status and notification streams.

Updated feedback layer:

- `frontend/src/design-system/feedback.tsx`
- `frontend/src/app/globals.css`
- `frontend/tests/contracts/design-system-contract.test.js`
- `docs/design-system/v148_realtime_notifications_ui.md`

Covered behavior:

- `DSLiveIndicator` displays connected, connecting, offline and error states;
- `DSNotificationFeed` renders normalized notification stream items;
- unread and tone-aware feed states are styled through shared CSS;
- the UI layer stays transport-agnostic for WebSocket, SSE or polling adapters;
- contract checks cover realtime notification exports and CSS classes.

## Command Palette / Fast Search

v149 adds a shared command palette primitive for Ctrl+K style search and quick actions.

Updated component layer:

- `frontend/src/design-system/components.tsx`
- `frontend/src/app/globals.css`
- `frontend/tests/contracts/design-system-contract.test.js`
- `docs/design-system/v149_command_palette.md`

Covered behavior:

- `DSCommandPalette` renders grouped commands and search results;
- the caller controls query state and selected actions;
- command items support descriptions, shortcuts, disabled states and tones;
- the UI layer does not own search sources, routing or permissions;
- contract checks cover command palette exports and CSS classes.

## Premium UX Completion

v150 closes the premium UX block with shared collaboration and activity primitives.

Updated collaboration layer:

- `frontend/src/design-system/feedback.tsx`
- `frontend/src/app/globals.css`
- `frontend/tests/contracts/design-system-contract.test.js`
- `docs/design-system/v150_premium_ux_completion.md`

Covered behavior:

- `DSPresenceStack` renders active collaborators with online, away and offline states;
- `DSActivityTimeline` renders recent team or record-level activity;
- activity items support tone-aware status indicators;
- mobile layouts keep collaboration widgets readable;
- contract checks cover v150 collaboration exports and CSS classes.

## Premium Brand Foundation

v151 upgrades the shared visual foundation for a premium SaaS and trainer marketplace experience.

Updated foundation:

- `frontend/src/app/globals.css`
- `frontend/src/design-system/tokens.ts`
- `frontend/src/app/layout.tsx`
- `docs/design-system/v151_premium_brand_foundation.md`

Covered behavior:

- premium token aliases for surfaces, muted colors, borders, radii, shadows and container width;
- reusable premium page, section, card, grid, metric, badge and CTA classes;
- premium glass panel and hero-ready utilities;
- commercial metadata for the public app shell.

## Premium Marketing Home Page

v152 replaces the starter homepage with a commercial TrainerHub marketing homepage.

Updated homepage layer:

- `frontend/src/app/page.tsx`
- `frontend/src/modules/public-storefront/components/marketing-home-page.tsx`
- `frontend/src/modules/public-storefront/components/hero-business-console.tsx`
- `frontend/src/modules/public-storefront/components/platform-map-section.tsx`
- `frontend/src/modules/public-storefront/components/role-workspace-section.tsx`
- `frontend/src/modules/public-storefront/components/commercial-proof-band.tsx`
- `frontend/src/modules/public-storefront/components/product-experience-timeline.tsx`
- `frontend/src/modules/public-storefront/components/final-premium-cta.tsx`
- `frontend/src/design-system/animated.tsx`
- `frontend/src/design-system/use-count-up.ts`
- `docs/design-system/v152_premium_marketing_home_page.md`

Covered behavior:

- strict dark premium hero for trainers and online fitness products;
- animated business console for revenue, students, sessions, progress and purchases;
- editorial pain section, platform map, role workspaces, proof band, animated timeline and cinematic CTA;
- scroll reveal sections, platform pulse, count-up metrics and reduced-motion support;
- responsive marketing layout for desktop, tablet and mobile.

## Premium Storefront Stabilization

v153 stabilizes the premium homepage contract and upgrades `/catalog` into a premium marketplace surface.

Updated storefront layer:

- `frontend/src/modules/public-storefront/components/marketplace-catalog-page.tsx`
- `frontend/src/modules/public-storefront/components/premium-marketplace-card.tsx`
- `frontend/src/app/globals.css`
- `frontend/src/design-system/animated.tsx`
- `frontend/src/design-system/use-count-up.ts`
- `docs/design-system/v153_premium_storefront_stabilization.md`
- `docs/design-system/v154_prep_marketplace_catalog_premium_foundation.md`

Covered behavior:

- homepage className/CSS contract stabilization;
- animated primitives exported from the design system;
- explicit reduced-motion fallback;
- premium catalog hero, featured product, filter bar and product grid;
- premium loading, empty and error states;
- trust/access explanation for marketplace purchases.

## Premium Product Detail Landing Pages

v154 turns `/catalog/programs/[slug]`, `/catalog/videos/[slug]` and `/catalog/bundles/[slug]` into premium product landing pages.

Updated product layer:

- `frontend/src/modules/public-storefront/components/content-detail-page.tsx`
- `frontend/src/modules/public-storefront/components/product-landing-hero.tsx`
- `frontend/src/modules/public-storefront/components/product-purchase-panel.tsx`
- `frontend/src/modules/public-storefront/components/product-includes-section.tsx`
- `frontend/src/modules/public-storefront/components/product-access-section.tsx`
- `docs/design-system/v154_premium_product_detail_landing_pages.md`

Covered behavior:

- premium product hero and product facts;
- sticky purchase panel with trust hints;
- “Что входит в доступ” and “Что происходит после оплаты” sections;
- trainer/author card and outcome cards;
- premium loading/error states and Russian SEO metadata.

## Premium App Shell and Checkout Page

v155 aligns the global public shell with the premium storefront and closes the primary purchase route.

Updated shell and checkout layer:

- `frontend/src/app/layout.tsx`
- `frontend/src/components/session-nav.tsx`
- `frontend/src/app/checkout/page.tsx`
- `frontend/src/app/checkout/success/page.tsx`
- `frontend/src/app/checkout/cancel/page.tsx`
- `frontend/src/modules/checkout/components/checkout-page.tsx`
- `frontend/src/modules/checkout/components/checkout-order-summary.tsx`
- `frontend/src/modules/checkout/components/checkout-payment-method.tsx`
- `frontend/src/modules/checkout/components/checkout-trust-panel.tsx`
- `frontend/src/modules/checkout/components/checkout-state-card.tsx`
- `docs/design-system/v155_premium_app_shell_checkout.md`

Covered behavior:

- global app shell without forced page container;
- compact role-aware header navigation;
- premium footer focused on public product and user entry points;
- checkout page with stable idempotency key, provider selection and order summary;
- Russian premium success and cancel states.

## Premium Customer Cabinet

v156 turns the post-purchase customer area into a unified premium workspace.

Updated customer layer:

- `frontend/src/modules/customer-cabinet/components/*`
- `frontend/src/app/cabinet/page.tsx`
- `frontend/src/app/customer/hub/page.tsx`
- `frontend/src/app/learning/page.tsx`
- `frontend/src/app/entitlements/page.tsx`
- `frontend/src/app/orders/page.tsx`
- `frontend/src/app/payments/page.tsx`
- `frontend/src/app/subscriptions/page.tsx`
- `frontend/src/app/billing/page.tsx`
- `frontend/src/app/messages/page.tsx`
- `docs/design-system/v156_premium_customer_cabinet.md`

Covered behavior:

- shared customer shell and internal navigation;
- premium customer dashboard at `/cabinet`;
- premium learning area, access cards, order/payment/subscription polish;
- finance and documents section without customer-facing technical labels;
- premium messages inbox with conversation list, thread and composer.

## Premium Trainer Cabinet

v157 turns the trainer area into a unified premium business workspace.

Updated trainer layer:

- `frontend/src/modules/trainer-cabinet/components/*`
- `frontend/src/modules/trainer-dashboard/components/trainer-dashboard-shell.tsx`
- `frontend/src/app/trainer/dashboard/page.tsx`
- `frontend/src/app/trainer/business/page.tsx`
- `frontend/src/app/trainer/videos/page.tsx`
- `frontend/src/app/trainer/reviews/page.tsx`
- `frontend/src/app/trainer/onboarding/page.tsx`
- `frontend/src/app/trainer/application-status/page.tsx`
- `docs/design-system/v157_premium_trainer_cabinet.md`

## Premium Trainer Product Builder

v157.1 repairs trainer shell integration, v158 upgrades product creation into a premium commercial builder, and v158.1 removes the remaining technical product and video studio windows, and v158.2 repairs upload-first usability, product material flow and layout overflow. v158.3 replaces narrow column layouts with horizontal product and video workbenches. v159 adds the shared premium profile workbench system and replaces customer/trainer sidebar shells with horizontal navigation. v159.1 repairs the dark profile scene, panel surfaces, rails, nav, panels and dark profile form controls. v159.2 removes nested vertical scrollbars and polishes profile workbench scrolling. v160 adds the premium media library picker and product publishing flow. v160.1 completes the product builder integration. v160.2 stabilizes the product/video flow before CRM and schedule work. v160.3 centralizes product media loading and starts the profile CSS layer split. v160.4 finishes the product media single source of truth so the product builder owns video library loading, retry, loading and error state. v161 rebuilds trainer CRM and schedule as premium operations workbenches. v162 upgrades trainer sales, finance and content analytics into premium workbenches. v163 completes trainer-facing education, reviews and payout request polish. v164 completes the trainer business cockpit, onboarding application and application status workbenches. v165 completes the trainer dashboard cockpit, video studio shell and route QA pass. v165.1 closes the final README/code/docs sync for the trainer cockpit and content studio. v165.2 finalizes the scoped CSS contract, README sync and trainer studio polish.

Updated product layer:

- `frontend/src/modules/trainer-products/components/trainer-product-builder-dashboard.tsx`
- `frontend/src/modules/upload/components/trainer-upload-panel.tsx`
- `frontend/src/modules/upload/components/trainer-content-studio.tsx`
- `frontend/src/modules/upload/components/trainer-video-upload-card.tsx`
- `frontend/src/modules/upload/components/trainer-content-card.tsx`
- `frontend/src/design-system/profile-workbench.tsx`
- `frontend/src/app/trainer/dashboard/assignments/page.tsx`
- `frontend/src/modules/trainer-sales/components/trainer-sales-dashboard.tsx`
- `frontend/src/modules/trainer-crm/components/trainer-crm-dashboard.tsx`
- `docs/design-system/v158_premium_trainer_product_builder.md`
- `docs/design-system/v158_1_product_builder_video_studio_repair.md`
- `docs/design-system/v158_2_product_video_usability_repair.md`
- `docs/design-system/v158_3_horizontal_workbench_rescue.md`
- `docs/design-system/v159_premium_profile_workbench.md`
- `docs/design-system/v159_1_profile_surface_repair.md`
- `docs/design-system/v159_2_nested_scrollbar_repair.md`
- `docs/design-system/v160_media_library_picker.md`
- `docs/design-system/v160_1_media_picker_integration.md`
- `docs/design-system/v160_2_product_video_flow_stabilization.md`
- `docs/design-system/v160_3_product_media_picker_cleanup.md`
- `docs/design-system/v160_4_product_media_single_source.md`
- `docs/design-system/v161_premium_trainer_operations.md`
- `docs/design-system/v162_premium_trainer_finance_analytics.md`
- `docs/design-system/v163_premium_trainer_education_reviews_payouts.md`
- `docs/design-system/v164_premium_trainer_business_onboarding_status.md`
- `docs/design-system/v165_premium_trainer_dashboard_video_route_qa.md`

## Demo Data / Seed Scenarios

v117 expands the demo seed layer for launch and smoke validation.

Seed command:

```bash
python scripts/bootstrap/seed_demo.py
```

Seed users:

- trainer: `trainer@example.com` / `trainer12345`
- student: `student@example.com` / `student12345`

Seed scenarios:

- trainer with products: published program, paid video and bundle;
- student with active course: paid order plus active entitlement;
- failed payment: failed order/payment scenario;
- refunded order: refunded bundle order/payment scenario;
- payout ready: trainer wallet, ledger credit and approved payout request;
- subscription expired: expired monthly subscription for the student.

The declarative seed contract lives in `backend/scripts/bootstrap/seed_demo.py`; the executable idempotent database seed lives in `scripts/bootstrap/seed_demo.py`.

## Public Marketplace Hardening

v118 adds stable public marketplace landing contracts on top of the existing catalog.

Public endpoints:

```http
GET /api/v1/public-catalog/
GET /api/v1/public-catalog/landing/<entity-type>/<slug>/
GET /api/v1/public-catalog/trainers/<trainer-slug>/landing/
```

The hardened marketplace payloads include:

- SEO title, description and canonical path;
- catalog, featured products and trainer attribution;
- product pricing and checkout CTA;
- review summary links;
- access/refund messaging tied to entitlement runtime;
- trainer profile, products, pricing and checkout CTA list.

Frontend support:

- `publicStorefrontApi.getMarketplaceHome()`;
- `publicStorefrontApi.getContentLanding(entityType, slug)`;
- `publicStorefrontApi.getTrainerLanding(slug)`.

## Launch Candidate

v119 adds the release candidate package.

Project version:

```text
v120-production-launch-pack
```

Launch candidate API:

```http
GET /api/v1/ops/admin/launch-candidate/
```

Launch candidate artifacts:

- `VERSION`
- `docs/launch/launch_candidate_v119.md`
- `scripts/ci/launch_gate.sh`
- `scripts/ci/production_gate.sh`
- `scripts/bootstrap/seed_demo.py`

Launch candidate payload includes:

- project version;
- smoke checklist;
- production environment checklist;
- known limitations;
- release notes;
- ship condition and next step.

## Production Launch Pack

v120 adds the final production launch documentation and handoff pack.

Production launch pack API:

```http
GET /api/v1/ops/admin/production-launch-pack/
```

Production docs:

- `docs/launch/production/deploy.md`
- `docs/launch/production/backup.md`
- `docs/launch/production/monitoring.md`
- `docs/launch/production/admin.md`
- `docs/launch/production/trainer.md`
- `docs/launch/production/student.md`
- `docs/launch/production/README.md`

Final gates:

- `bash scripts/ci/production_gate.sh`
- `bash scripts/ci/launch_gate.sh`
- `cd backend && python manage.py check_production_readiness --json --fail-on-degraded`

Release state:

- previous stage: `v119-launch-candidate`
- current stage: `v120-production-launch-pack`
- next step: production deployment

## Role Matrix / Permission Audit

v107 adds backend-level role enforcement for operations APIs. Access is no longer treated as a UI-only concern.

Roles:

- `admin` — full operations access and write authority.
- `trainer` — trainer dashboard/content/customer workflows.
- `student` / `user` — learning, billing, assignments and messaging self-service.
- `support` — read access to payment/audit/ops surfaces, notification resend/system-message support actions where allowed.
- `finance` — payment read access and payout/finance operations.
- `readonly_auditor` — read-only audit, payment, payout and ops visibility.

API-level enforcement:

- payments admin uses `IsAdminSupportFinanceReadonly`;
- payout admin uses `IsFinanceOps`;
- audit admin uses `IsAuditReader`;
- ops admin/readiness views use method-aware admin/support/finance/readonly access;
- notification admin uses `IsNotificationOperator`;
- system messages are limited to admin/support via `IsAdminOrSupport`.

## Tenant Isolation Hardening

v108 adds runtime tenant scoping for commerce and operations data. Tenant membership is resolved through `TenantMembership.account_id`, mapped to active `Tenant.owner_account_id`, then applied to trainer-owned rows.

Runtime scoping covers:

- orders through order item/payment trainer metadata;
- payments through order item/payment trainer metadata;
- payment webhook events through linked payments;
- entitlements through source order and entitlement metadata;
- payout requests and payout balance entries through trainer wallet ownership.

Self-service buyer endpoints still filter strictly by `request.user`. Global admins keep platform-wide visibility, while support/finance/readonly auditor roles require explicit tenant membership to see tenant rows.

## Admin Global Search

v109 adds a tenant-aware admin search endpoint:

```http
GET /api/v1/ops/admin/global-search/?q=<query>&categories=users,orders,payments&limit=10
```

Search categories:

- `users`
- `trainers`
- `orders`
- `payments`
- `payouts`
- `content`
- `subscriptions`

Each result includes `category`, `entity_type`, `entity_id`, `title`, `subtitle`, `status`, `href`, and metadata. Global admins can search platform-wide; support/finance/readonly operators only see tenant-scoped rows.

## Support Console

v110 adds support operations endpoints:

```http
GET /api/v1/ops/admin/support-console/?email=<user-email>
POST /api/v1/ops/admin/support-console/notifications/resend/
POST /api/v1/ops/admin/support-console/entitlements/fix/
```

The support console exposes a tenant-scoped user snapshot with:

- user card;
- orders;
- payments;
- entitlements;
- failed/rejected/ignored webhook events;
- notification deliveries.

Support actions:

- resend a notification delivery by resetting it to `pending`;
- grant a manual entitlement with `source_type=admin_grant`;
- revoke an entitlement;
- record every action in audit with the support/admin operator as actor.

## Disputes / Chargebacks

v111 adds finance/admin chargeback operations:

```http
POST /api/v1/disputes/admin/chargebacks/open/
POST /api/v1/disputes/admin/chargebacks/<operation-id>/evidence/
POST /api/v1/disputes/admin/chargebacks/<operation-id>/resolve/
```

Chargeback lifecycle coverage:

- dispute opened from a payment;
- linked `DisputeCase` and `ChargebackOperation`;
- payment/order risk state through the existing payment service;
- automatic `access_hold` metadata on active order entitlements;
- runtime access denial while the hold is active;
- evidence submission with operator/timestamp metadata;
- won outcome releases payout risk hold and entitlement access hold;
- lost outcome marks payment/order as charged back and revokes entitlements;
- admin audit trail for opened/evidence/won/lost actions.

## Finance Documents

v112 activates the finance documents module and adds admin finance document operations:

```http
GET /api/v1/finance-documents/admin/documents/
POST /api/v1/finance-documents/admin/documents/build/
GET /api/v1/finance-documents/admin/documents/accountant-export/
POST /api/v1/finance-documents/admin/documents/<document-id>/finalize/
```

Supported document types:

- `invoice`
- `receipt`
- `credit_note`
- `refund_document`
- `payout_act`
- `statement`

Finance document coverage:

- invoice and receipt generation from order/payment;
- credit note and refund document generation from payment/refund context;
- immutable document numbers;
- rendered HTML artifact body on generation;
- admin/finance API permissions;
- CSV export for accountant workflows;
- audit trail for generated commercial documents.

## Tax / Legal Compliance

v113 activates the legal compliance module and adds runtime consent tracking:

```http
GET /api/v1/legal/me/documents/
POST /api/v1/legal/me/documents/<document-id>/accept/
GET /api/v1/legal/me/compliance-status/
GET /api/v1/legal/me/consent-logs/
```

Legal compliance coverage:

- active terms of service acceptance;
- active privacy policy acceptance;
- active refund policy acceptance;
- trainer agreement acceptance for trainer actor checks;
- consent logs with IP, user agent, document version and source;
- compliance status showing missing required documents;
- invoice legal payload fields from KYC/finance profile snapshots.

## Observability Runtime

v114 adds production runtime observability endpoints:

```http
GET /api/v1/observability/runtime/
GET /api/v1/ops/admin/observability-runtime/
```

Runtime health coverage:

- webhook failure rate;
- payment error rate;
- payout repair/manual review rate;
- background job failures and outbox backlog;
- health indicators for admin dashboards;
- admin ops alerts with severity, code, detail and values.

## Ops Runbooks

v115 adds production incident runbooks and an admin runbook index:

```http
GET /api/v1/ops/admin/runbooks/
GET /api/v1/ops/admin/runbooks/<runbook-key>/
```

Runbooks:

- failed payment webhook;
- wrong entitlement;
- payout mismatch;
- refund conflict;
- database restore;
- deployment rollback.

Each runbook includes trigger, triage, repair/procedure, verification and escalation steps.

## CI/CD Production Gate

v116 adds a dedicated production gate script and CI job:

```bash
bash scripts/ci/production_gate.sh
```

The gate runs:

- backend syntax compilation;
- Django system check;
- Django deploy/security check;
- migration drift check;
- full backend pytest;
- backend contract tests;
- production readiness command;
- backend dependency integrity check;
- frontend install, typecheck and build;
- frontend contract tests;
- frontend dependency audit at high severity or above.

## Backend Modules

Installed/runtime modules:

- Commerce: `orders`, `payments`, `payouts`, `subscriptions`, `purchases`, `billing`, `entitlements`, `finance_documents`, `legal_compliance`.
- Learning/content: `trainer_cms`, `content`, `videos`, `products`, `assignments`, `progress`, `reviews`, `messaging`.
- Trainer/customer: `users`, `accounts`, `authn`, `customers`, `trainers`, `trainer_profiles`, `onboarding`, `favorites`, `public_catalog`, `categories`, `referrals`, `habits`.
- Operations: `audit`, `ops`, `events`, `workflows`, `projections`, `observability`, `analytics`, `moderation`, `notifications`, `platform_settings`.

Present but not fully wired in the active runtime settings yet:

- `affiliates`, `cohorts`, `common`, `disputes`, `finance_reporting`, `gamification`, `live_sessions`, `promotions`.

## Frontend Modules

Admin modules:

- `admin-payments`, `admin-payouts`, `admin-subscriptions`, `admin-audit`, `admin-operations`, `admin-reconciliation`, `admin-reconciliation-snapshots`, `admin-trainer-applications`, `admin-entity-details`, `admin-shell`.

Customer/student modules:

- `customer-billing`, `customer-hub`, `access-center`, `student-learning`, `content-runtime`, `assignments`, `messaging`, `notifications`, `payments`, `subscriptions`, `checkout`, `progress`.

Trainer modules:

- `trainer-dashboard`, `trainer-products`, `trainer-sales`, `trainer-crm`, `trainer-booking`, `trainer-revenue`, `trainer-payouts`, `trainer-analytics`, `trainer-onboarding`, `upload`, `trainers`.

Public marketplace modules:

- `public-storefront`, `reviews`, `referrals`, `auth`.

## Main User Surfaces

Admin:

- `/admin/payouts` — payout operations, integrity issues, repair preview/history, exports, ops health.
- `/admin/payments` — payments, webhook events, refunds, entitlement status, reconciliation issues.
- `/admin/subscriptions` — subscription lifecycle operations, trial/active/past due/cancelled/expired state overview.
- `/admin/audit` — audit logs, filters, retention tooling, CSV export.
- `/admin/notifications` — notification center, announcements, templates, delivery health, projection health.

Customer:

- `/learning` — student learning area with courses, programs, lessons, materials, and runtime lesson access.
- `/assignments` — homework list, answer submission, trainer review status, score/comment feedback.
- `/messages` — trainer-student inbox, direct conversations, message sending and read state.
- `/billing` — purchases, subscriptions, payment statuses, invoices/receipts-ready data, active access.
- `/subscriptions` — subscription state, renewal projection, lifecycle actions.
- `/cabinet` — customer account hub with billing and access entry points.

Trainer:

- `/trainer/dashboard/products` — course/program builder, lesson materials, paid product editor, readiness and publish actions.
- `/trainer/dashboard/assignments` — homework creation, student submissions, trainer review, score/comment feedback.
- `/trainer/reviews` — review quality dashboard, low-rating visibility, public trainer replies.
- `/trainer/dashboard/sales` — sales, revenue, refunds, conversion-oriented metrics, student access signals.
- `/trainer/dashboard/crm` — customer cards, purchase/access/attendance history, trainer notes, client segments.
- `/trainer/dashboard/schedule` — availability rules, generated slots, reservations, cancellations, waitlist.
- `/trainer/dashboard/schedule` — attendance check-in, no-show, checkout history, QR token and Mifare-ready identifiers.
- `/trainer/payouts` and payout-related dashboard links — payout request and payout status flows.

## Run Commands

Backend:

```bash
cd backend
python manage.py migrate
python manage.py runserver
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Local demo data:

```bash
python scripts/bootstrap/seed_demo.py
```

## Verification Commands

Backend smoke:

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py check_production_readiness --json
bash scripts/ci/launch_gate.sh
```

Targeted roadmap tests:

```bash
cd backend
pytest tests/test_notifications_v91_domain_triggers.py tests/test_customer_crm_v92.py tests/test_booking_v93_schedule_waitlist.py tests/test_booking_v94_attendance_checkin.py tests/test_production_readiness_v95.py tests/test_course_program_builder_v97.py tests/test_content_access_runtime_v98.py tests/test_video_delivery_hardening_v99.py tests/test_student_learning_area_v100.py tests/test_progress_tracking_v101.py tests/test_assignments_homework_v102.py tests/test_reviews_feedback_loop_v103.py tests/test_messaging_core_v104.py tests/test_role_matrix_permissions_v107.py tests/test_tenant_isolation_v108.py tests/test_admin_global_search_v109.py tests/test_support_console_v110.py tests/test_disputes_chargebacks_v111.py tests/test_finance_documents_v112.py tests/test_legal_compliance_v113.py tests/test_observability_runtime_v114.py tests/test_ops_runbooks_v115.py tests/test_ci_cd_production_gate_v116.py tests/test_demo_seed_scenarios_v117.py tests/test_public_marketplace_hardening_v118.py tests/test_launch_candidate_v119.py tests/test_production_launch_pack_v120.py
```

Frontend:

```bash
cd frontend
npm run typecheck
npm run build
```

Current local limitation:

- In this workspace, `python3 -m pytest ...` fails before execution because backend Python dependencies are not installed in the active environment (`django` / `rest_framework`).
- `python3 -m py_compile ...`, `git diff --check`, and `npm run typecheck` were used for local verification.

## Payout Module

The payout module is production-oriented after v77.

Implemented capabilities:

- payout integrity snapshots;
- repair preview before execution;
- controlled repair execution;
- repair audit history;
- reconciliation report export;
- repair audit export;
- payout admin dashboard hardening;
- total/pending/failed payout counters;
- integrity issue counters;
- last repair run;
- health indicators;
- payout paid notification event.

Important API areas:

- `GET /api/v1/payouts/admin-ops/summary/`
- `GET /api/v1/payouts/admin-ops/reconciliation/snapshot/`
- `GET /api/v1/payouts/admin-ops/requests/export.csv`
- `GET /api/v1/payouts/admin-ops/ledger/export.csv`
- payout admin transition actions including approve, processing, mark-paid, reject, bulk transitions, risk hold release, repair execution.

## Payments, Orders, Entitlements

The payment block is hardened through v91.

Implemented capabilities:

- webhook signature validation;
- replay protection;
- duplicate webhook detection;
- webhook audit trail;
- payment idempotency;
- successful payment finalization;
- entitlement activation after successful payment;
- partial and full refunds;
- refund audit trail;
- entitlement revocation after full refund;
- payment reconciliation across provider payments, internal payments, and entitlements;
- admin payment operations UI;
- customer billing UI;
- trainer sales dashboard.

Important API areas:

- `GET /api/v1/payments-admin/`
- payment confirm/fail/refund actions;
- payment webhook ingestion;
- customer billing data consumed by `/billing`;
- entitlement access checks used by content/video guards.

## Course / Program Builder

The content builder block started at v97.

Implemented capabilities:

- course draft CRUD in `trainer_cms`;
- ordered course lessons;
- lesson video asset links;
- lesson materials as structured JSON entries;
- program lessons now support the same materials payload;
- course publish history through `ContentVersion`;
- trainer dashboard counters include course drafts;
- `/trainer/dashboard/products` includes a Course / Program Builder panel.

Important API areas:

- `GET/POST /api/v1/trainer-cms/courses/`
- `GET/PATCH/POST /api/v1/trainer-cms/courses/{id}/`
- `POST /api/v1/trainer-cms/courses/{id}/publish/`
- `GET/POST /api/v1/trainer-cms/courses/{id}/lessons/`
- `GET/PATCH/DELETE /api/v1/trainer-cms/courses/{id}/lessons/{lesson_id}/`

## Content Access Runtime

v98 adds the runtime access layer used when a student opens a lesson.

Implemented capabilities:

- protected program lesson runtime;
- protected course lesson runtime for v97 course drafts;
- preview lessons can open without authentication;
- active program/course entitlements unlock protected lesson fields;
- expired or refunded access returns a blocked payload and hides video/materials;
- trainer owner and admin inspection paths are explicit;
- runtime responses include v90 access audit rules for operations/debugging;
- frontend `contentRuntimeApi` client is ready for the future student learning area.

Important API areas:

- `GET /api/v1/content/runtime/programs/{program_slug}/lessons/{lesson_ref}/`
- `GET /api/v1/content/runtime/courses/{course_id}/lessons/{lesson_id}/`

## Video Delivery Hardening

v99 hardens protected video playback URL issuance.

Implemented capabilities:

- short-lived signed playback leases around presigned storage URLs;
- video access logs for granted and denied playback attempts;
- access token hashes stored server-side, raw tokens returned only to the caller;
- request metadata capture: IP, user agent, referer, origin;
- entitlement decision snapshot stored with each access log;
- anti-leeching referer/origin checks with warning telemetry;
- denied refunded/expired access attempts are logged without issuing a token.

Important API areas:

- `POST /api/v1/videos/{video_id}/access-url/`

## Student Learning Area

v100 adds the student-facing learning cabinet.

Implemented capabilities:

- `/learning` page for students;
- read model for active courses, programs, videos, lessons, and materials;
- next lesson shortcut;
- inline runtime lesson opening through v98 access checks;
- progress state from v101 lesson tracking;
- unresolved access diagnostics for refunded/expired/broken entitlements;
- navigation from customer hub and global authenticated nav.

Important API areas:

- `GET /api/v1/content/student/learning-area/`

## Progress Tracking

v101 adds learning progress tracking.

Implemented capabilities:

- lesson completed API;
- program/course progress percent;
- completed lesson state in `/learning`;
- next lesson skips completed lessons;
- last activity timestamp on program/course progress;
- trainer visibility endpoint for student progress across owned programs/courses;
- progress API is now mounted under `/api/v1/progress/`.

Important API areas:

- `POST /api/v1/progress/lessons/complete/`
- `GET /api/v1/progress/programs/`
- `GET /api/v1/progress/summary/`
- `GET /api/v1/progress/trainer/students/`

## Assignments / Homework

v102 adds homework on top of the content and entitlement runtime.

Implemented capabilities:

- assignment model for program/course homework;
- student answer submissions with attachments-ready payloads;
- trainer review with status, comment, and score;
- active entitlement check before a student can see or submit homework;
- student `/assignments` page;
- trainer `/trainer/dashboard/assignments` page;
- assignment API is mounted under `/api/v1/assignments/`.

Important API areas:

- `GET /api/v1/assignments/student/`
- `POST /api/v1/assignments/student/{assignment_id}/submit/`
- `GET /api/v1/assignments/trainer/`
- `POST /api/v1/assignments/trainer/`
- `GET /api/v1/assignments/trainer/submissions/`
- `POST /api/v1/assignments/trainer/submissions/{submission_id}/review/`

## Reviews / Feedback Loop

v103 completes the review loop for courses, trainers, moderation, rating aggregation, and trainer replies.

Implemented capabilities:

- course targets can now be reviewed with active entitlement verification;
- published review summaries include rating distribution;
- storefront review panel shows rating breakdown and public trainer replies;
- trainer review quality page supports public replies to reviews;
- admin moderation remains the publishing gate;
- review API exposes a trainer reply endpoint.

Important API areas:

- `GET /api/v1/reviews/{target_type}/{target_id}/`
- `POST /api/v1/reviews/{target_type}/{target_id}/`
- `POST /api/v1/reviews/admin/{review_id}/moderate/`
- `GET /api/v1/reviews/trainer/quality/`
- `POST /api/v1/reviews/trainer/{review_id}/reply/`

## Messaging Core

v104 adds the trainer-student messaging core.

Implemented capabilities:

- direct trainer-student conversations;
- user and system messages;
- unread counters and mark-read flow;
- message events;
- in-app notification hook for recipients;
- domain event/outbox hook for `messaging.message_sent`;
- `/messages` frontend inbox.

Important API areas:

- `GET /api/v1/messaging/me/inbox/`
- `POST /api/v1/messaging/conversations/start/`
- `GET /api/v1/messaging/conversations/{conversation_id}/messages/`
- `POST /api/v1/messaging/conversations/{conversation_id}/send/`
- `POST /api/v1/messaging/conversations/{conversation_id}/mark-read/`
- `POST /api/v1/messaging/conversations/{conversation_id}/system/`

## Launch Hardening

v105 closes the content-learning launch block.

Implemented capabilities:

- production readiness gate updated to `v105`;
- role matrix included in readiness output;
- new API contracts for learning, progress, homework, reviews and messaging;
- launch gate script for CI and local release checks;
- CI `launch-hardening` and `production-gate` jobs;
- readiness seed data and smoke command registry updated.

Important commands:

- `cd backend && python manage.py check_production_readiness --json --fail-on-degraded`
- `bash scripts/ci/launch_gate.sh`

## Subscription Lifecycle

Subscriptions now support an explicit lifecycle:

- `trial`
- `active`
- `past_due`
- `cancelled`
- `expired`

Implemented lifecycle behavior:

- trial access policy;
- active and past_due access policy while the paid period is current;
- renewal webhook handling;
- entitlement synchronization;
- cancellation and resume flows;
- due expiration reconciliation;
- admin expiring-subscription notification batch.

Important API areas:

- `GET /api/v1/subscriptions/center/`
- `GET /api/v1/subscriptions/lifecycle-policy/`
- `GET /api/v1/subscriptions/lifecycle-summary/`
- `GET /api/v1/subscriptions/{id}/renewal-projection/`
- `POST /api/v1/subscriptions/{id}/sync-entitlements/`
- `POST /api/v1/subscriptions/admin/reconcile-entitlements/`
- `POST /api/v1/subscriptions/admin/expire-due/`
- `POST /api/v1/subscriptions/admin/notify-expiring/`

## Access Guard Hardening

Runtime access checks are now routed through the entitlement access audit policy instead of ad hoc purchase checks.

Covered access decisions:

- API permission-level checks;
- video/content access;
- expired entitlement block;
- refund revoke block;
- chargeback and cancelled source block;
- trial and past_due subscription access while the current period is still valid.

## Notifications

v91 adds domain notifications for core commerce events.

Notification events:

- successful payment;
- payment failed;
- refund processed;
- access opened;
- subscription activated;
- subscription expiring;
- payout paid.

Notification hardening:

- in-app notification creation;
- email delivery queue support;
- fallback skipped email delivery when a template is not configured;
- idempotency by `metadata.event_key`;
- outbox projection coverage for payment refund and subscription expiring events;
- admin projection health endpoint remains available in notification admin tooling.

New event-level delivery types:

- `payment_succeeded`
- `payment_refunded`
- `access_granted`
- `subscription_expiring`
- `payout_paid`

## CRM Core

v92 adds the first production CRM layer for trainers.

Implemented capabilities:

- customer card;
- purchase history;
- access and entitlement history;
- booking/attendance history from existing reservations;
- trainer-private notes;
- client segments;
- segment assignment;
- trainer CRM frontend dashboard.

Important API areas:

- `GET /api/v1/customer/trainer-crm/`
- `GET /api/v1/customer/trainer-crm/{customer_id}/`
- `POST /api/v1/customer/trainer-crm/notes/`
- `POST /api/v1/customer/trainer-crm/segments/`
- `POST /api/v1/customer/trainer-crm/segments/assign/`

New UI:

- `/trainer/dashboard/crm`

## Booking / Schedule

v93 hardens the existing booking app into a trainer schedule surface.

Implemented capabilities:

- trainer booking profile;
- availability rules;
- generated slots from availability;
- slot capacity limits;
- customer reservation creation;
- reservation cancellation;
- waitlist join;
- automatic promotion from waitlist when a confirmed reservation is cancelled;
- trainer schedule dashboard.

Important API areas:

- `GET /api/v1/booking/me/profile/`
- `GET /api/v1/booking/me/availability-rules/`
- `POST /api/v1/booking/me/availability-rules/`
- `GET /api/v1/booking/me/schedule/`
- `POST /api/v1/booking/me/generate-slots/`
- `GET /api/v1/booking/slots/open/`
- `POST /api/v1/booking/reservations/create/`
- `POST /api/v1/booking/reservations/waitlist/`
- `POST /api/v1/booking/reservations/{reservation_id}/cancel/`

New UI:

- `/trainer/dashboard/schedule`

## Attendance / Check-in

v94 adds studio-ready attendance tracking on top of booking reservations.

Implemented capabilities:

- expected attendance record for every confirmed reservation;
- manual check-in;
- QR-ready check-in token;
- Mifare-ready external identifier check-in;
- check-out and duration calculation;
- no-show marking;
- attendance history in trainer schedule;
- attendance data in CRM customer history.

Important API areas:

- `GET /api/v1/booking/attendance/`
- `POST /api/v1/booking/attendance/check-in/`
- `POST /api/v1/booking/attendance/check-out/{attendance_id}/`
- `POST /api/v1/booking/attendance/no-show/`

Frontend:

- `/trainer/dashboard/schedule` now includes check-in, check-out, no-show and attendance history controls.

## Production Readiness

v95 adds a full-platform read-only production readiness gate.

Implemented checks:

- permissions audit for sensitive admin/trainer surfaces;
- API contract checks for current roadmap endpoints;
- Python symbol/import contract checks;
- regression test file presence checks;
- seed data helper presence check;
- CI workflow presence check;
- smoke command manifest;
- management command gate.

Important API areas:

- `GET /api/v1/ops/admin/production-readiness/`

Management command:

```bash
cd backend
python manage.py check_production_readiness --json
python manage.py check_production_readiness --json --fail-on-degraded
```

Recommended v95 smoke suite:

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
pytest tests/test_customer_crm_v92.py tests/test_booking_v93_schedule_waitlist.py tests/test_booking_v94_attendance_checkin.py tests/test_notifications_v91_domain_triggers.py tests/test_production_readiness_v95.py

cd ../frontend
npm run typecheck
npm run build
```

## Migrations Added In This Line

- `backend/apps/subscriptions/migrations/0004_v89_subscription_trial_status.py`
- `backend/apps/notifications/migrations/0003_v91_notification_event_types.py`
- `backend/apps/customers/migrations/0003_v92_crm_core.py`
- `backend/apps/booking/migrations/0002_v93_booking_schedule_core.py`
- `backend/apps/booking/migrations/0003_v94_attendance_checkin.py`

Run migrations before using the new lifecycle and notification states:

```bash
cd backend
python manage.py migrate
```

## Verification

Checks used during this version line:

```bash
python3 -m py_compile <changed backend files>
git diff --check
cd frontend && npm run typecheck
```

Frontend routes were also smoke-checked through the local Next.js dev server:

- `/admin/payments`
- `/billing`
- `/trainer/dashboard/sales`
- `/trainer/dashboard/crm`
- `/trainer/dashboard/schedule`
- `/subscriptions`

Known local environment limitation:

- `python3 -m pytest ...` currently fails in this workspace before test execution with `ModuleNotFoundError: No module named 'django'`.
- The committed tests are present, but the local Python environment needs Django/test dependencies installed before pytest can run.

## Recent Commits

- `d9e11de` — Implement CRM booking attendance and readiness roadmap
- `5ec315c` — Document current v91 roadmap state
- `fac1fba` — Implement payment admin billing and notification roadmap
- `9fa2da7` — Implement payout ops and payment lifecycle hardening

## Release Gate

Before production release, run:

- permissions audit;
- API contract tests;
- smoke tests;
- seed data verification;
- docs update;
- CI green gate.

See also:

- `MANIFEST.md` — current module/file manifest.
- `BUILD_REPORT.md` — current validation report and known local limitations.
