# TrainerHub — current version v91

TrainerHub is a trainer commerce platform with admin operations, customer billing, trainer sales, payout controls, subscriptions, entitlements, audit trails, and notifications.

This README describes the current roadmap state after the payout production pass and the Payment / Orders / Entitlements block.

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

The next planned block starts at v92 — CRM Core.

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

## Migrations Added In This Line

- `backend/apps/subscriptions/migrations/0004_v89_subscription_trial_status.py`
- `backend/apps/notifications/migrations/0003_v91_notification_event_types.py`

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
- `/subscriptions`

Known local environment limitation:

- `python3 -m pytest ...` currently fails in this workspace before test execution with `ModuleNotFoundError: No module named 'django'`.
- The committed tests are present, but the local Python environment needs Django/test dependencies installed before pytest can run.

## Recent Commits

- `fac1fba` — Implement payment admin billing and notification roadmap
- `9fa2da7` — Implement payout ops and payment lifecycle hardening

## Next Roadmap

Planned next versions:

- v92 — CRM Core
- v93 — Booking / Schedule
- v94 — Attendance / Check-in
- v95 — Production Readiness Pass

Before production release, run a full readiness pass:

- permissions audit;
- API contract tests;
- smoke tests;
- seed data verification;
- docs update;
- CI green gate.
