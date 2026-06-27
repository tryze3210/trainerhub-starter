# Database restore

## Trigger
- Data corruption, failed migration, accidental destructive operation, or infrastructure loss.
- Production readiness or runtime health cannot recover through app-level repair.

## Preconditions
- Confirm incident commander approval.
- Freeze deploys and background repair jobs.
- Identify target restore point and affected services.

## Procedure
1. Stop web and worker processes that write to Postgres.
2. Take a final emergency backup if the database is reachable.
3. Restore the approved backup into an isolated database first.
4. Run migration drift check and smoke queries against the isolated restore.
5. Point production to the restored database or promote the restored instance.
6. Restart web, workers and scheduler in controlled order.

## Verification
- `python manage.py check` passes.
- Production readiness gate is not critical.
- Observability runtime shows background jobs and webhooks recovering.
- Spot-check users, payments, entitlements, payouts and audit events.

## Escalation
- Keep finance/support informed when payment, payout or entitlement data may be stale.
- File a post-incident report with restore point, data loss window and follow-up actions.
