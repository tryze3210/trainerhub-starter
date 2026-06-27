# Refund conflict

## Trigger
- Payment refund succeeded, but entitlement or payout state did not update.
- Partial refund amount does not match internal ledger reversal.
- Full refund and chargeback/dispute overlap.

## Triage
1. Open payment admin for the payment.
2. Check refund operations in `payment.provider_payload`.
3. Check order status, entitlements and payout ledger reversals.
4. Check dispute/chargeback state before applying any access change.

## Repair
1. For duplicate refund webhook, verify idempotency key/refund id and avoid a second reversal.
2. For partial refund, confirm only the proportional payout reversal was created.
3. For full refund, confirm entitlements are revoked and subscriptions cancelled.
4. If chargeback exists, use chargeback resolution flow instead of refund repair.

## Verification
- Payment status and refund operations match provider.
- Entitlements match refund policy.
- Payout reversal exists once for each refund id.
- Audit trail includes refund/repair actor and reason.

## Escalation
- Escalate to finance for provider/internal amount mismatch.
- Escalate to support when access messaging must be sent to the customer.
