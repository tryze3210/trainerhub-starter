# Deployment rollback

## Trigger
- New deployment causes critical health, payment, entitlement, payout or login regression.
- CI passed, but production runtime health degrades after release.

## Preconditions
- Identify current release SHA and previous known-good SHA.
- Confirm database migrations are backward-compatible or prepare database restore path.
- Pause non-essential scheduled jobs if they amplify the incident.

## Procedure
1. Announce rollback in the incident channel.
2. Stop or drain workers if the release changes background job semantics.
3. Deploy the previous known-good image/SHA.
4. Restart web, worker and scheduler processes.
5. If migration rollback is required, follow the database restore runbook instead of ad hoc SQL.

## Verification
- `/api/v1/runtime/health/` and `/api/v1/runtime/readiness/` are healthy.
- `/api/v1/ops/admin/observability-runtime/` no longer reports critical status.
- Payment webhook intake, checkout and entitlement runtime smoke tests pass.
- Error rate returns to baseline.

## Escalation
- Escalate to engineering lead if rollback does not restore health in 15 minutes.
- Escalate to finance/support when customer payments or access were affected.
