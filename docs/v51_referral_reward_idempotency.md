# TrainerHub v51 — referral reward idempotency hardening

## Why this patch exists

Payment webhooks are delivered with at-least-once semantics. The marketplace must treat `order_paid` referral rewards as a financial write and protect it with deterministic idempotency.

This patch makes the reward business key explicit:

```text
ReferralAttribution + trigger_type + trigger_reference
```

For the paid-order flow, `trigger_type` is `order_paid` and `trigger_reference` must be the order id.

## What changed

- `ReferralRewardService.reward_for_paid_order(...)` is now idempotent.
- Duplicate calls with the same attribution/order return the existing reward.
- Duplicate calls do not append another `ReferralLedger` entry.
- A database unique constraint protects against duplicate rewards even if a caller bypasses the service.
- Percent-based referral programs now calculate reward from `order_amount`.

## Migration safety note

The migration adds:

```text
ref_reward_once_per_trigger
```

If a local database already contains duplicate rewards for the same attribution/trigger/reference, clean duplicates before running `migrate`.

Inspection query for PostgreSQL:

```sql
select attribution_id, trigger_type, trigger_reference, count(*)
from referrals_referralreward
group by attribution_id, trigger_type, trigger_reference
having count(*) > 1;
```
