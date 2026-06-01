# v50 referrals integration notes

## Architectural decision

Referrals remain a bounded context. Auth, checkout and payments do not manipulate referral models directly; they call `ReferralIntegrationService`.

## Why not signals

Signals are deliberately avoided. Signup and payment success are commercial state transitions; hidden side effects through Django signals make idempotency and tests worse. Explicit service calls are easier to reason about and later to move behind an outbox consumer.

## Idempotency

Reward idempotency is based on:

```text
trigger_type = order_paid
trigger_reference = <order.id>
```

This matches payment webhook retry semantics: if the same external event arrives twice, payment success handling may be called twice, but reward accrual returns the existing reward.

## Future v51

The next production step is a reconciliation/reporting layer for referrals:

- admin list/filter for rewards and ledger;
- reversal on refund/chargeback;
- dashboard metrics by program/code/campaign;
- payout bridge from referral ledger to finance/payout ledger.
