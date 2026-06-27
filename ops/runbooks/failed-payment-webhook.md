# Failed payment webhook

## Trigger
- `observability.runtime.webhooks.status` is `degraded` or `critical`.
- `PaymentWebhookEvent.status` is `failed` or `rejected`.
- Customer paid at provider, but internal order/payment is not finalized.

## Triage
1. Open `/api/v1/ops/admin/observability-runtime/`.
2. Check `/api/v1/payments-webhooks/?status=failed`.
3. Compare provider payload with internal `payment_id`, `external_payment_id` and event id.
4. Confirm the webhook is not a duplicate/replay rejection.

## Repair
1. Reprocess the webhook from the payment admin webhook action if the signature and payload are valid.
2. If reprocessing still fails, use the support console to inspect the customer snapshot.
3. If payment succeeded at provider but access is missing, run the audited reconciliation repair for `grant_order_access`.

## Verification
- Payment status is `succeeded`.
- Order status is `paid` or `completed`.
- Entitlements exist and pass runtime access check.
- New audit event references the operator and repair reason.

## Escalation
- Escalate to finance if provider payload cannot be matched to an internal payment.
- Escalate to engineering if failures repeat for the same provider/event type.
