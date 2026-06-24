# TrainerHub — current version v95

TrainerHub is a trainer commerce platform with admin operations, customer billing, trainer sales, payout controls, subscriptions, entitlements, audit trails, and notifications.

This README describes the current roadmap state after the payout production pass, the Payment / Orders / Entitlements block, CRM Core, Booking / Schedule, Attendance / Check-in, and the Production Readiness Pass.

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

The v70-v95 production-readiness roadmap is now closed at the platform gate level.

## Main User Surfaces

Admin:

- `/admin/payouts` — payout operations, integrity issues, repair preview/history, exports, ops health.
- `/admin/payments` — payments, webhook events, refunds, entitlement status, reconciliation issues.
- `/admin/subscriptions` — subscription lifecycle operations, trial/active/past due/cancelled/expired state overview.
- `/admin/audit` — audit logs, filters, retention tooling, CSV export.
- `/admin/notifications` — notification center, announcements, templates, delivery health, projection health.

Customer:

- `/billing` — purchases, subscriptions, payment statuses, invoices/receipts-ready data, active access.
- `/subscriptions` — subscription state, renewal projection, lifecycle actions.
- `/cabinet` — customer account hub with billing and access entry points.

Trainer:

- `/trainer/dashboard/sales` — sales, revenue, refunds, conversion-oriented metrics, student access signals.
- `/trainer/dashboard/crm` — customer cards, purchase/access/attendance history, trainer notes, client segments.
- `/trainer/dashboard/schedule` — availability rules, generated slots, reservations, cancellations, waitlist.
- `/trainer/dashboard/schedule` — attendance check-in, no-show, checkout history, QR token and Mifare-ready identifiers.
- `/trainer/payouts` and payout-related dashboard links — payout request and payout status flows.

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

- `fac1fba` — Implement payment admin billing and notification roadmap
- `9fa2da7` — Implement payout ops and payment lifecycle hardening

## Release Gate

The v70-v95 roadmap block is complete. Before production release, run:

- permissions audit;
- API contract tests;
- smoke tests;
- seed data verification;
- docs update;
- CI green gate.
