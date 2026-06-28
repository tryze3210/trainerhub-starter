# MANIFEST — TrainerHub v156

This manifest describes the current repository state after v156 Premium Customer Cabinet and All Customer Sections.

## Current Version

- Current roadmap version: `v156`
- Closed block: `v70-v95`
- Closed launch block: `v97-v105` content, learning, progress, messaging, launch hardening
- Closed UX block: `v131-v150` UX redesign and premium experience
- Current storefront block: `v151-v156` premium brand foundation, marketing homepage, marketplace catalog, product detail landing pages, checkout shell and customer cabinet
- Recent local roadmap commits include content-learning, messaging and launch-hardening blocks through v105.

## Core Backend Modules

Runtime modules in active Django settings:

- `accounts`
- `analytics`
- `assignments`
- `audit`
- `authn`
- `billing`
- `booking`
- `categories`
- `challenges`
- `content`
- `core`
- `customers`
- `entitlements`
- `events`
- `favorites`
- `finance_documents`
- `habits`
- `legal_compliance`
- `media_assets`
- `messaging`
- `moderation`
- `notifications`
- `observability`
- `onboarding`
- `orders`
- `ops`
- `payments`
- `payouts`
- `platform_settings`
- `products`
- `progress`
- `projections`
- `public_catalog`
- `purchases`
- `referrals`
- `reviews`
- `subscriptions`
- `trainer_cms`
- `trainer_profiles`
- `trainers`
- `users`
- `videos`
- `workflows`

Present backend apps that are not fully represented in the active settings module yet:

- `affiliates`
- `cohorts`
- `common`
- `disputes`
- `finance_reporting`
- `gamification`
- `live_sessions`
- `promotions`

Backend ownership groups:

Commercial and access:

- `payments`
- `payouts`
- `subscriptions`
- `entitlements`
- `notifications`
- `customers`
- `booking`
- `reviews`
- `messaging`
- `videos`
- `content`
- `trainer_cms`
- `products`
- `progress`
- `assignments`
- `messaging`

Operations modules:

- `audit`
- `ops`
- `access_control`
- `events`
- `workflows`
- `analytics`
- `moderation`
- `platform_settings`

Trainer/customer modules:

- `trainers`
- `trainer_profiles`
- `customers`
- `favorites`
- `public_catalog`
- `referrals`
- `promotions`

Role matrix modules and contracts:

- `backend/apps/access_control/permissions.py` — backend permission classes for admin, trainer, student, support, finance and readonly auditor roles.
- `backend/apps/access_control/selectors.py` — role capabilities and feature matrix.
- `backend/apps/accounts/models.py` — active role assignments including support, finance and readonly auditor.
- `backend/apps/accounts/migrations/0002_v107_role_matrix.py` — v107 role choices migration.
- `backend/tests/test_role_matrix_permissions_v107.py` — method-aware role matrix regression tests.

Tenant isolation modules and contracts:

- `backend/apps/tenancy/scoping.py` — tenant-aware queryset scoping helpers for commerce, entitlements and payouts.
- `backend/tests/test_tenant_isolation_v108.py` — cross-tenant leakage regression tests.

Admin global search modules and contracts:

- `backend/apps/ops/admin_global_search.py` — tenant-aware search across users, trainers, orders, payments, payouts, content and subscriptions.
- `backend/apps/ops/api/views.py` — `AdminGlobalSearchView`.
- `backend/tests/test_admin_global_search_v109.py` — search coverage and tenant-scope regression tests.
- `frontend/src/modules/admin-operations/api.ts` — frontend API client method for global search.

Support console modules and contracts:

- `backend/apps/ops/support_console.py` — support snapshot, notification resend and manual entitlement fix logic.
- `backend/apps/ops/api/views.py` — support console API endpoints.
- `backend/tests/test_support_console_v110.py` — support console snapshot/action/audit regression tests.
- `frontend/src/modules/admin-operations/api.ts` — frontend API client methods for support console actions.

Disputes and chargebacks modules and contracts:

- `backend/apps/disputes/services/case_service.py` — chargeback open/evidence/resolve service with entitlement hold and audit trail.
- `backend/apps/disputes/api/views.py` — finance/admin chargeback operation endpoints.
- `backend/apps/disputes/api/urls.py` — chargeback lifecycle URL contracts.
- `backend/apps/entitlements/access_audit.py` — runtime block for entitlements with `access_hold` metadata.
- `backend/tests/test_disputes_chargebacks_v111.py` — chargeback lifecycle, access hold and API regression tests.

Finance document modules and contracts:

- `backend/apps/finance_documents/models/documents.py` — invoices, receipts, credit notes, refund documents, payout acts and statements.
- `backend/apps/finance_documents/services/commercial_documents.py` — commercial document generation and accountant CSV export.
- `backend/apps/finance_documents/api/views.py` — admin finance document build/list/finalize/export endpoints.
- `backend/apps/finance_documents/migrations/0003_v112_document_types.py` — v112 document type choices migration.
- `backend/tests/test_finance_documents_v112.py` — finance document generation/export/API regression tests.

Legal compliance modules and contracts:

- `backend/apps/legal_compliance/models.py` — legal document templates, acceptance snapshots, consent logs, KYC and eligibility snapshots.
- `backend/apps/legal_compliance/services/acceptance.py` — required policy acceptance and compliance status service.
- `backend/apps/legal_compliance/api/views.py` — legal documents, accept, compliance status and consent log endpoints.
- `backend/apps/legal_compliance/migrations/0001_initial.py` — active legal compliance schema.
- `backend/tests/test_legal_compliance_v113.py` — policy acceptance, consent log and invoice legal field regression tests.

Observability runtime modules and contracts:

- `backend/apps/observability/runtime.py` — production runtime health snapshot for webhooks, payments, payout repairs and background jobs.
- `backend/apps/observability/api/views.py` — direct observability runtime endpoint.
- `backend/apps/ops/api/views.py` — admin ops mirror endpoint for observability runtime.
- `backend/tests/test_observability_runtime_v114.py` — runtime health, alert and API contract regression tests.

Ops runbook modules and contracts:

- `backend/apps/ops/runbooks.py` — required production runbook index and detail loader.
- `backend/apps/ops/api/views.py` — admin runbook index/detail endpoints.
- `ops/runbooks/failed-payment-webhook.md` — failed payment webhook runbook.
- `ops/runbooks/wrong-entitlement.md` — wrong entitlement runbook.
- `ops/runbooks/payout-mismatch.md` — payout mismatch runbook.
- `ops/runbooks/refund-conflict.md` — refund conflict runbook.
- `ops/runbooks/database-restore.md` — database restore runbook.
- `ops/runbooks/deployment-rollback.md` — deployment rollback runbook.
- `backend/tests/test_ops_runbooks_v115.py` — runbook index/content/API regression tests.

CI/CD production gate modules and contracts:

- `.github/workflows/ci.yml` — CI workflow with `backend-quality`, `frontend-build`, `launch-hardening` and `production-gate` jobs.
- `scripts/ci/production_gate.sh` — production gate script for backend tests, frontend typecheck/build, contract tests, migration check and security checks.
- `scripts/ci/launch_gate.sh` — launch hardening gate including v119 contract coverage.
- `backend/tests/test_ci_cd_production_gate_v116.py` — CI/CD production gate regression tests.

Demo data / seed scenario modules and contracts:

- `backend/scripts/bootstrap/seed_demo.py` — declarative v117 launch seed payload.
- `scripts/bootstrap/seed_demo.py` — idempotent local database seed for demo trainer, student, products, commerce, entitlement, payout and subscription scenarios.
- `backend/tests/test_demo_seed_scenarios_v117.py` — demo seed scenario contract tests.

Public marketplace hardening modules and contracts:

- `backend/apps/public_catalog/services.py` — marketplace home, content landing and trainer landing payload builders with SEO, pricing, reviews and checkout CTAs.
- `backend/apps/public_catalog/api/views.py` — public marketplace home/content/trainer landing endpoints.
- `backend/apps/public_catalog/api/urls.py` — v118 public URL contracts.
- `frontend/src/modules/public-storefront/api.ts` — frontend client methods for marketplace home, content landing and trainer landing payloads.
- `backend/tests/test_public_marketplace_hardening_v118.py` — public marketplace hardening contract tests.

Launch candidate modules and contracts:

- `VERSION` — project version marker for the current release candidate.
- `docs/launch/launch_candidate_v119.md` — human-readable release candidate note, smoke checklist and production environment checklist.
- `backend/apps/ops/launch_candidate.py` — structured launch candidate pack builder.
- `backend/apps/ops/api/views.py` — `AdminLaunchCandidateView`.
- `backend/apps/ops/api/urls.py` — `ops-admin-launch-candidate` URL contract.
- `backend/tests/test_launch_candidate_v119.py` — launch candidate regression tests.

Production launch pack modules and contracts:

- `docs/launch/production/README.md` — production launch pack index.
- `docs/launch/production/deploy.md` — deploy procedure and post-deploy checks.
- `docs/launch/production/backup.md` — backup and restore guide.
- `docs/launch/production/monitoring.md` — monitoring and alert routing guide.
- `docs/launch/production/admin.md` — admin/support/finance guide.
- `docs/launch/production/trainer.md` — trainer guide.
- `docs/launch/production/student.md` — student guide.
- `backend/apps/ops/production_launch_pack.py` — structured production launch pack builder.
- `backend/apps/ops/api/views.py` — `AdminProductionLaunchPackView`.
- `backend/apps/ops/api/urls.py` — `ops-admin-production-launch-pack` URL contract.
- `backend/tests/test_production_launch_pack_v120.py` — production launch pack regression tests.

UI design system modules and contracts:

- `frontend/src/design-system/tokens.ts` — shared frontend design tokens, including premium brand foundation aliases.
- `frontend/src/design-system/components.tsx` — shared UI primitives for buttons, cards, forms, tables, modal shell, command palette and statistics cards.
- `frontend/src/design-system/feedback.tsx` — shared skeleton, empty state, toast, live indicator, notification feed, presence stack, activity timeline, transition and status feedback primitives.
- `frontend/src/design-system/layouts.tsx` — shared layout primitives for admin, trainer, student, public and mobile layouts.
- `frontend/src/design-system/library.tsx` — shared DataTable, chart, premium chart, draggable Kanban, calendar, upload, rich text, video and statistics catalog.
- `frontend/src/design-system/theme.tsx` — light/dark, brand palette and white-label runtime theme engine.
- `frontend/src/design-system/index.ts` — design-system public exports.
- `frontend/src/app/globals.css` — semantic CSS variables, premium utilities, aliases and shared interaction states.
- `frontend/tests/contracts/design-system-contract.test.js` — v131-v156 design-system contract test.
- `docs/design-system/v131_ui_design_system.md` — v131 design-system notes.
- `docs/design-system/v132_layout_system.md` — v132 layout-system notes.
- `docs/design-system/v133_component_library.md` — v133 component-library notes.
- `docs/design-system/v134_theme_engine.md` — v134 theme-engine notes.
- `docs/design-system/v135_motion_ui_polish.md` — v135 motion/ui polish notes.
- `docs/design-system/v146_premium_charts.md` — v146 premium chart notes.
- `docs/design-system/v147_drag_drop_kanban.md` — v147 drag-and-drop Kanban notes.
- `docs/design-system/v148_realtime_notifications_ui.md` — v148 realtime notifications UI notes.
- `docs/design-system/v149_command_palette.md` — v149 command palette notes.
- `docs/design-system/v150_premium_ux_completion.md` — v150 premium UX completion notes.
- `docs/design-system/v151_premium_brand_foundation.md` — v151 premium brand foundation notes.
- `docs/design-system/v152_premium_marketing_home_page.md` — v152 premium marketing homepage notes.
- `docs/design-system/v153_premium_storefront_stabilization.md` — v153 premium storefront stabilization notes.
- `docs/design-system/v154_prep_marketplace_catalog_premium_foundation.md` — v154-prep marketplace catalog foundation notes.
- `docs/design-system/v154_premium_product_detail_landing_pages.md` — v154 premium product detail landing notes.
- `docs/design-system/v155_premium_app_shell_checkout.md` — v155 premium shell and checkout notes.
- `docs/design-system/v156_premium_customer_cabinet.md` — v156 premium customer cabinet notes.

Admin dashboard redesign modules:

- `frontend/src/app/admin/page.tsx` — v136 admin cockpit using shared design-system primitives.

Trainer workspace redesign modules:

- `frontend/src/modules/trainer-dashboard/components/trainer-dashboard-shell.tsx` — v137 trainer layout and side navigation using shared primitives.
- `frontend/src/app/trainer/dashboard/page.tsx` — v137 trainer dashboard using shared statistics, chart, section and feedback primitives.

CRM redesign modules:

- `frontend/src/modules/trainer-crm/components/trainer-crm-dashboard.tsx` — v138 trainer CRM dashboard using shared table, form, section and feedback primitives.

Booking redesign modules:

- `frontend/src/modules/trainer-booking/components/trainer-booking-dashboard.tsx` — v139 trainer booking dashboard using shared calendar, table, form, section and feedback primitives.

Payments redesign modules:

- `frontend/src/modules/admin-payments/components/admin-payment-operations-dashboard.tsx` — v140 admin payment operations dashboard using shared table, form, statistics, section and feedback primitives.

Payouts redesign modules:

- `frontend/src/modules/admin-payouts/components/admin-payout-operations-dashboard.tsx` — v141 admin payout operations dashboard shell using shared card, statistics, section, skeleton and status primitives.

Student portal redesign modules:

- `frontend/src/app/customer/hub/page.tsx` — v142 customer/student marketplace hub using shared header, statistics, section, skeleton and feedback primitives.

Learning experience redesign modules:

- `frontend/src/app/learning/page.tsx` — v143 student learning area using shared header, statistics, section, skeleton and feedback primitives.

Public marketplace redesign modules:

- `frontend/src/modules/public-storefront/components/marketplace-catalog-page.tsx` — v144 public catalog using shared header, form, badge, section, skeleton and feedback primitives.

Mobile responsive pass modules:

- `frontend/src/app/globals.css` — v145 mobile responsive hardening for shared layout, cards, tables, calendar, Kanban, modal, toast, upload and rich text primitives.
- `frontend/tests/contracts/design-system-contract.test.js` — v145 mobile CSS contract checks.

Premium charts modules:

- `frontend/src/design-system/library.tsx` — v146 premium line chart, donut chart and insight chart card primitives.
- `frontend/src/app/globals.css` — v146 premium chart, line chart, donut chart and mobile chart styling.
- `frontend/tests/contracts/design-system-contract.test.js` — v146 premium chart contract checks.
- `docs/design-system/v146_premium_charts.md` — v146 premium chart implementation notes.

Drag-and-drop Kanban modules:

- `frontend/src/design-system/library.tsx` — v147 Kanban move payload and native drag/drop event hooks.
- `frontend/src/app/globals.css` — v147 Kanban draggable card and dropzone states.
- `frontend/tests/contracts/design-system-contract.test.js` — v147 Kanban drag/drop contract checks.
- `docs/design-system/v147_drag_drop_kanban.md` — v147 Kanban drag/drop implementation notes.

Realtime notifications UI modules:

- `frontend/src/design-system/feedback.tsx` — v148 live indicator and notification feed primitives.
- `frontend/src/app/globals.css` — v148 realtime indicator, notification feed, unread and mobile feed states.
- `frontend/tests/contracts/design-system-contract.test.js` — v148 realtime notification UI contract checks.
- `docs/design-system/v148_realtime_notifications_ui.md` — v148 realtime notification UI implementation notes.

Command palette modules:

- `frontend/src/design-system/components.tsx` — v149 controlled command palette and command item types.
- `frontend/src/app/globals.css` — v149 command palette overlay, grouped results, shortcut and mobile styles.
- `frontend/tests/contracts/design-system-contract.test.js` — v149 command palette contract checks.
- `docs/design-system/v149_command_palette.md` — v149 command palette implementation notes.

Premium UX completion modules:

- `frontend/src/design-system/feedback.tsx` — v150 collaborator presence stack and activity timeline primitives.
- `frontend/src/app/globals.css` — v150 presence, collaborator status, activity timeline and mobile collaboration styles.
- `frontend/tests/contracts/design-system-contract.test.js` — v150 premium UX completion contract checks.
- `docs/design-system/v150_premium_ux_completion.md` — v150 premium UX completion notes.

Premium brand foundation modules:

- `frontend/src/design-system/tokens.ts` — v151 premium token aliases for surfaces, shadows, radii and layout.
- `frontend/src/app/globals.css` — v151 premium page, section, card, grid, badge, metric and CTA utilities.
- `frontend/src/app/layout.tsx` — v151 commercial public metadata.
- `docs/design-system/v151_premium_brand_foundation.md` — v151 premium brand foundation notes.

Premium marketing homepage modules:

- `frontend/src/app/page.tsx` — v152 public homepage entrypoint.
- `frontend/src/modules/public-storefront/components/marketing-home-page.tsx` — v152 homepage composition.
- `frontend/src/modules/public-storefront/components/hero-business-console.tsx` — v152 animated premium dashboard preview.
- `frontend/src/modules/public-storefront/components/platform-map-section.tsx` — v152 platform module map with pulse state.
- `frontend/src/modules/public-storefront/components/role-workspace-section.tsx` — v152 split role workspace panels.
- `frontend/src/modules/public-storefront/components/commercial-proof-band.tsx` — v152 commercial proof metrics.
- `frontend/src/modules/public-storefront/components/product-experience-timeline.tsx` — v152 animated product workflow timeline.
- `frontend/src/modules/public-storefront/components/final-premium-cta.tsx` — v152 cinematic final CTA.
- `frontend/src/design-system/animated.tsx` — v152 scroll reveal primitives.
- `frontend/src/design-system/use-count-up.ts` — v152 animated count-up helper.
- `docs/design-system/v152_premium_marketing_home_page.md` — v152 premium homepage notes.

Premium storefront stabilization modules:

- `frontend/src/modules/public-storefront/components/marketplace-catalog-page.tsx` — v153 premium marketplace catalog page.
- `frontend/src/modules/public-storefront/components/premium-marketplace-card.tsx` — v153 premium product card.
- `frontend/src/app/globals.css` — v153 catalog hero, featured product, filter, card, state and trust styles.
- `frontend/tests/contracts/design-system-contract.test.js` — v153 premium storefront contract checks.
- `docs/design-system/v153_premium_storefront_stabilization.md` — v153 storefront stabilization notes.
- `docs/design-system/v154_prep_marketplace_catalog_premium_foundation.md` — v154-prep marketplace foundation notes.

Premium product detail landing modules:

- `frontend/src/modules/public-storefront/components/content-detail-page.tsx` — v154 product detail orchestrator.
- `frontend/src/modules/public-storefront/components/product-landing-hero.tsx` — v154 product hero.
- `frontend/src/modules/public-storefront/components/product-purchase-panel.tsx` — v154 sticky purchase panel.
- `frontend/src/modules/public-storefront/components/product-includes-section.tsx` — v154 includes section.
- `frontend/src/modules/public-storefront/components/product-outcome-section.tsx` — v154 outcome section.
- `frontend/src/modules/public-storefront/components/product-trainer-section.tsx` — v154 trainer card.
- `frontend/src/modules/public-storefront/components/product-access-section.tsx` — v154 access timeline.
- `frontend/src/modules/public-storefront/components/product-detail-skeleton.tsx` — v154 premium loading state.
- `frontend/src/modules/public-storefront/components/product-detail-state.tsx` — v154 premium error state.
- `frontend/src/modules/public-storefront/components/product-detail-utils.ts` — v154 product detail labels, facts and fallbacks.
- `frontend/src/app/catalog/programs/[slug]/page.tsx` — v154 Russian program metadata.
- `frontend/src/app/catalog/videos/[slug]/page.tsx` — v154 Russian video metadata.
- `frontend/src/app/catalog/bundles/[slug]/page.tsx` — v154 Russian bundle metadata.

Premium app shell and checkout modules:

- `frontend/src/app/layout.tsx` — v155 app shell, premium header, premium main and premium footer.
- `frontend/src/components/session-nav.tsx` — v155 compact role-aware header navigation.
- `frontend/src/app/checkout/page.tsx` — v155 checkout route.
- `frontend/src/app/checkout/success/page.tsx` — v155 Russian premium success state.
- `frontend/src/app/checkout/cancel/page.tsx` — v155 Russian premium cancel state.
- `frontend/src/modules/checkout/components/checkout-page.tsx` — v155 checkout composition and API flow.
- `frontend/src/modules/checkout/components/checkout-order-summary.tsx` — v155 order summary and price formatting.
- `frontend/src/modules/checkout/components/checkout-payment-method.tsx` — v155 provider selector.
- `frontend/src/modules/checkout/components/checkout-trust-panel.tsx` — v155 purchase trust panel.
- `frontend/src/modules/checkout/components/checkout-state-card.tsx` — v155 checkout auth/loading state card.
- `docs/design-system/v155_premium_app_shell_checkout.md` — v155 implementation notes.

Premium customer cabinet modules:

- `frontend/src/modules/customer-cabinet/components/customer-cabinet-shell.tsx` — v156 customer workspace shell.
- `frontend/src/modules/customer-cabinet/components/customer-cabinet-nav.tsx` — v156 internal customer navigation.
- `frontend/src/modules/customer-cabinet/components/customer-dashboard-card.tsx` — v156 customer section card.
- `frontend/src/modules/customer-cabinet/components/customer-status-badge.tsx` — v156 customer status badge.
- `frontend/src/modules/customer-cabinet/components/customer-empty-state.tsx` — v156 empty state.
- `frontend/src/modules/customer-cabinet/components/customer-loading-state.tsx` — v156 loading state.
- `frontend/src/modules/customer-cabinet/components/customer-error-state.tsx` — v156 error state.
- `frontend/src/modules/customer-cabinet/components/customer-metric-card.tsx` — v156 metric card.
- `frontend/src/modules/customer-cabinet/components/customer-section-header.tsx` — v156 section header.
- `frontend/src/modules/customer-cabinet/components/customer-format.ts` — v156 Russian labels and formatting helpers.
- `frontend/src/app/cabinet/page.tsx` — v156 main customer dashboard.
- `frontend/src/app/customer/hub/page.tsx` — v156 extended customer overview.
- `frontend/src/app/learning/page.tsx` — v156 premium learning area.
- `frontend/src/app/entitlements/page.tsx` — v156 customer access center.
- `frontend/src/app/orders/page.tsx` — v156 customer orders.
- `frontend/src/app/payments/page.tsx` — v156 customer payments.
- `frontend/src/app/subscriptions/page.tsx` — v156 customer subscriptions.
- `frontend/src/app/billing/page.tsx` — v156 finance and documents section.
- `frontend/src/app/messages/page.tsx` — v156 premium inbox.
- `docs/design-system/v156_premium_customer_cabinet.md` — v156 implementation notes.

## Roadmap Status

| Version | Area | Status |
| --- | --- | --- |
| v70-v77 | Payout integrity and ops hardening | Done |
| v80-v91 | Payments, billing, subscriptions, notifications | Done |
| v92-v95 | CRM, booking, attendance, production readiness | Done |
| v96-v105 | Content, learning, assignments, reviews, messaging, launch hardening | Done |
| v106 | Documentation final sync | Done |
| v107 | Role matrix / permission audit | Done |
| v108 | Tenant isolation hardening | Done |
| v109 | Admin global search | Done |
| v110 | Support console | Done |
| v111 | Disputes / chargebacks | Done |
| v112 | Finance documents | Done |
| v113 | Tax / legal compliance | Done |
| v114 | Observability runtime | Done |
| v115 | Ops runbooks | Done |
| v116 | CI/CD production gate | Done |
| v117 | Demo data / seed scenarios | Done |
| v118 | Public marketplace hardening | Done |
| v119 | Launch candidate | Done |
| v120 | Production launch pack | Done |
| v131 | UI design system | Done |
| v132 | Layout system | Done |
| v133 | Component library | Done |
| v134 | Theme engine | Done |
| v135 | Motion / UI polish | Done |
| v136 | Admin dashboard | Done |
| v137 | Trainer workspace | Done |
| v138 | CRM | Done |
| v139 | Booking | Done |
| v140 | Payments | Done |
| v141 | Payouts | Done |
| v142 | Student portal | Done |
| v143 | Learning experience | Done |
| v144 | Public marketplace | Done |
| v145 | Mobile responsive pass | Done |
| v146 | Premium charts | Done |
| v147 | Drag and drop Kanban | Done |
| v148 | Realtime notifications UI | Done |
| v149 | Command palette / fast search | Done |
| v150 | Premium UX completion | Done |
| v151 | Premium brand foundation | Done |
| v152 | Premium marketing homepage | Done |
| v153 | Premium storefront stabilization | Done |
| v154-prep | Marketplace catalog premium foundation | Done |
| v154 | Premium product detail landing pages | Done |
| v155 | Premium app shell, footer cleanup and checkout page | Done |
| v156 | Premium customer cabinet and all customer sections | Current |

## Current Frontend Modules

- `admin-payments`
- `admin-payouts`
- `admin-subscriptions`
- `customer-billing`
- `customer-hub`
- `student-learning`
- `assignments`
- `messaging`
- `notifications`
- `subscriptions`
- `trainer-sales`
- `trainer-crm`
- `trainer-booking`
- `trainer-dashboard`
- `trainer-products`
- `trainer-revenue`
- `trainer-payouts`
- `public-storefront`
- `checkout`
- `payments`

## Current Frontend Routes

Admin:

- `/admin`
- `/admin/audit`
- `/admin/notifications`
- `/admin/operations`
- `/admin/payments`
- `/admin/payouts`
- `/admin/reconciliation`
- `/admin/reconciliation/snapshots`
- `/admin/subscriptions`

Customer:

- `/billing`
- `/cabinet`
- `/customer/access`
- `/customer/hub`
- `/learning`
- `/assignments`
- `/messages`
- `/entitlements`
- `/notifications`
- `/orders`
- `/payments`
- `/subscriptions`

Trainer:

- `/trainer/dashboard`
- `/trainer/dashboard/analytics`
- `/trainer/dashboard/assignments`
- `/trainer/dashboard/crm`
- `/trainer/dashboard/payouts`
- `/trainer/dashboard/products`
- `/trainer/dashboard/revenue`
- `/trainer/dashboard/sales`
- `/trainer/dashboard/schedule`
- `/trainer/onboarding`
- `/trainer/videos`

Marketplace/public:

- `/catalog`
- `/catalog/bundles/[slug]`
- `/catalog/programs/[slug]`
- `/catalog/videos/[slug]`
- `/trainers`
- `/trainers/[slug]`

## Recent Roadmap Files Added

Migrations:

- `backend/apps/subscriptions/migrations/0004_v89_subscription_trial_status.py`
- `backend/apps/notifications/migrations/0003_v91_notification_event_types.py`
- `backend/apps/customers/migrations/0003_v92_crm_core.py`
- `backend/apps/booking/migrations/0002_v93_booking_schedule_core.py`
- `backend/apps/booking/migrations/0003_v94_attendance_checkin.py`
- `backend/apps/trainer_cms/migrations/0002_v97_course_program_builder.py`
- `backend/apps/content/migrations/0002_v98_lesson_materials.py`
- `backend/apps/entitlements/migrations/0005_v98_course_target_choice.py`
- `backend/apps/videos/migrations/0003_v99_video_access_log.py`
- `backend/apps/progress/migrations/0001_v101_progress_tracking.py`
- `backend/apps/assignments/migrations/0001_v102_assignments_homework.py`
- `backend/apps/reviews/migrations/0004_v103_feedback_loop.py`
- `backend/apps/messaging/migrations/0001_v104_messaging_core.py`

Documentation:

- `README.md` — current state, roadmap table, backend/frontend module map
- `MANIFEST.md` — repository manifest and roadmap inventory
- `BUILD_REPORT.md` — verification summary, launch gate and next roadmap block

Backend services/read models:

- `backend/apps/customers/selectors.py` — trainer CRM selector
- `backend/apps/booking/services/attendance.py` — booking attendance/check-in service
- `backend/apps/trainer_cms/api/views.py` — course/program builder API
- `backend/apps/trainer_cms/services.py` — course publish version snapshots
- `backend/apps/content/runtime.py` — lesson access runtime
- `backend/apps/content/student_learning.py` — student learning area read model
- `backend/apps/content/api/views.py` — runtime lesson endpoints
- `backend/apps/videos/services/issue_access_url.py` — signed playback leases and delivery logs
- `backend/apps/progress/services.py` — lesson completion and course/program progress
- `backend/apps/progress/selectors.py` — student/trainer progress read models
- `backend/apps/assignments/services.py` — homework submission and trainer review rules
- `backend/apps/assignments/selectors.py` — student/trainer homework read models
- `backend/apps/assignments/api/views.py` — assignment and submission endpoints
- `backend/apps/reviews/services.py` — review moderation and trainer reply loop
- `backend/apps/reviews/selectors.py` — course review target resolution and rating aggregation
- `backend/apps/reviews/api/views.py` — review moderation, trainer quality and reply endpoints
- `backend/apps/messaging/services/conversations.py` — direct conversations, unread counters, notification hooks
- `backend/apps/messaging/selectors/inbox.py` — messaging inbox and message payloads
- `backend/apps/messaging/api/views.py` — messaging inbox, send, read and system-message endpoints
- `backend/apps/ops/production_readiness.py` — v105 launch readiness, role matrix, API contracts and smoke commands
- `backend/apps/ops/production_readiness.py` — v95 readiness gate
- `backend/apps/ops/management/commands/check_production_readiness.py`

Frontend modules:

- `frontend/src/modules/admin-payments/`
- `frontend/src/modules/customer-billing/`
- `frontend/src/modules/trainer-sales/`
- `frontend/src/modules/trainer-crm/`
- `frontend/src/modules/trainer-booking/`
- `frontend/src/modules/trainer-products/components/course-program-builder-panel.tsx`
- `frontend/src/modules/upload/api.ts` — trainer CMS course draft client
- `frontend/src/modules/content-runtime/api.ts` — student lesson runtime client
- `frontend/src/modules/student-learning/api.ts`
- `frontend/src/modules/progress/api.ts`
- `frontend/src/modules/assignments/api.ts`
- `frontend/src/modules/reviews/api.ts`
- `frontend/src/modules/messaging/api.ts`
- `frontend/src/components/storefront-reviews-panel.tsx`
- `frontend/src/app/learning/page.tsx`
- `frontend/src/app/assignments/page.tsx`
- `frontend/src/app/messages/page.tsx`
- `frontend/src/app/trainer/dashboard/assignments/page.tsx`

Tests:

- `backend/tests/test_notifications_v91_domain_triggers.py`
- `backend/tests/test_payment_admin_v86.py`
- `backend/tests/test_customer_crm_v92.py`
- `backend/tests/test_booking_v93_schedule_waitlist.py`
- `backend/tests/test_booking_v94_attendance_checkin.py`
- `backend/tests/test_production_readiness_v95.py`
- `backend/tests/test_course_program_builder_v97.py`
- `backend/tests/test_content_access_runtime_v98.py`
- `backend/tests/test_video_delivery_hardening_v99.py`
- `backend/tests/test_student_learning_area_v100.py`
- `backend/tests/test_progress_tracking_v101.py`
- `backend/tests/test_assignments_homework_v102.py`
- `backend/tests/test_reviews_feedback_loop_v103.py`
- `backend/tests/test_messaging_core_v104.py`
- `backend/tests/test_production_readiness_v95.py` — updated to assert v105 launch gate

Launch hardening:

- `.github/workflows/ci.yml` — includes `launch-hardening`
- `scripts/ci/launch_gate.sh`

## Commands

Run backend:

```bash
cd backend
python manage.py migrate
python manage.py runserver
```

Run frontend:

```bash
cd frontend
npm install
npm run dev
```

Readiness:

```bash
cd backend
python manage.py check_production_readiness --json
python manage.py check_production_readiness --json --fail-on-degraded
```

Frontend verification:

```bash
cd frontend
npm run typecheck
npm run build
```

## Intentionally Not Included

- `node_modules`
- `frontend/tsconfig.tsbuildinfo`
- `__pycache__`
- `.pyc`
- local virtualenvs
- local database files
