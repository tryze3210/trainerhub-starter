# MANIFEST — TrainerHub v105

This manifest describes the current repository state after v105 Launch Hardening.

## Current Version

- Current roadmap version: `v105`
- Closed block: `v70-v95`
- Closed launch block: `v97-v105` content, learning, progress, messaging, launch hardening
- Latest local roadmap commit before v101: `d9e11de Implement CRM booking attendance and readiness roadmap`

## Core Backend Modules

Commercial and access modules:

- `orders`
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
