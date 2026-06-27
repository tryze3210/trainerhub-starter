# MANIFEST — TrainerHub v120

This manifest describes the current repository state after v120 Production Launch Pack.

## Current Version

- Current roadmap version: `v120`
- Closed block: `v70-v95`
- Closed launch block: `v97-v105` content, learning, progress, messaging, launch hardening
- Active planning block: production launch pack complete
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
| v120 | Production launch pack | Current |

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
