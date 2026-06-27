# Payout mismatch

## Trigger
- Payout integrity snapshot reports critical issues.
- Trainer wallet totals differ from ledger entries.
- Payout repair preview shows manual review rows.

## Triage
1. Open `/api/v1/payouts/admin-ops/integrity/`.
2. Review `/api/v1/payouts/admin-ops/repair/preview/`.
3. Check risk holds and recent payout repair history.
4. Identify whether mismatch is reserve, release, accrual, reversal or wallet total drift.

## Repair
1. Execute only deterministic repair actions through `/api/v1/payouts/admin-ops/repair/execute/`.
2. For manual review rows, export repair history and attach evidence to the finance ticket.
3. Do not edit wallet totals directly.

## Verification
- Integrity snapshot returns no critical issue for the repaired entity.
- Repair audit export contains operator, actions and result.
- Trainer available/locked/paid balances reconcile to ledger.

## Escalation
- Escalate to finance lead for shortfall or already-paid payout conflicts.
- Escalate to engineering if deterministic repair creates a new mismatch.
