# TrainerHub — current version v103

TrainerHub is a trainer commerce platform with admin operations, customer billing, trainer sales, payout controls, subscriptions, entitlements, audit trails, notifications, CRM, booking, attendance, and production-readiness checks.

This README describes the current roadmap state after v103 Reviews / Feedback Loop. The v70-v95 platform-readiness block is closed; the content-learning product block now tracks lesson completion, learning progress, homework, submissions, reviews, moderation, rating aggregation, and trainer feedback.

## Current Roadmap State

Completed in the current line:

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

The v70-v95 production-readiness roadmap is now closed at the platform gate level.

Next roadmap:

- v104 — Messaging Core
- v105 — Launch Hardening

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
```

Targeted roadmap tests:

```bash
cd backend
pytest tests/test_notifications_v91_domain_triggers.py tests/test_customer_crm_v92.py tests/test_booking_v93_schedule_waitlist.py tests/test_booking_v94_attendance_checkin.py tests/test_production_readiness_v95.py tests/test_course_program_builder_v97.py tests/test_content_access_runtime_v98.py tests/test_video_delivery_hardening_v99.py tests/test_student_learning_area_v100.py tests/test_progress_tracking_v101.py tests/test_assignments_homework_v102.py tests/test_reviews_feedback_loop_v103.py
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
