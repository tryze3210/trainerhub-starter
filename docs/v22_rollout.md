# v22 rollout

## 1. Schema
Add finance app tables:
- settlement transactions
- reconciliation sessions
- discrepancies
- outbox events
- webhook inbox

## 2. Extend payouts app
Ensure `PayoutBatch` has fields:
- `external_reference` char/varchar nullable
- `exported_at` datetime nullable
- `paid_at` datetime nullable

## 3. Provider adapter registration
Introduce a registry, for example:
```python
FINANCE_PROVIDER_GATEWAYS = {
    "manual": ManualSettlementGateway(),
    # "yookassa": YooKassaSettlementGateway(...),
}
```

## 4. Webhook endpoint
Public endpoint example:
- `POST /api/v1/webhooks/finance/{provider}/`

Flow:
- verify signature
- resolve gateway by provider code
- call `ProviderWebhookService(gateway).handle_event(...)`
- return 200 on idempotent duplicates too

## 5. Periodic jobs
- export draft batches eligible for payout
- poll providers where webhooks are not enough
- daily reconciliation for previous day and month-to-date
- outbox dispatcher

## 6. Ops / observability
Metrics you need immediately:
- settlement exports count
- failed settlement transactions count
- open discrepancies count
- unresolved discrepancy age
- outbox lag seconds

## 7. Repair governance
Do not expose free-form finance repair endpoints to trainers.
Only finance admins should resolve or force-settle discrepancies.
Every repair action must leave outbox/audit trail.
