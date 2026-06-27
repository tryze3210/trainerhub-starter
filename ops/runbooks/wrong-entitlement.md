# Wrong entitlement

## Trigger
- Customer reports missing or incorrect access.
- Support console shows entitlement mismatch.
- Content runtime returns `access_required`, `source_order_invalid`, `entitlement_access_held`, or an unexpected target id.

## Triage
1. Open `/api/v1/ops/admin/support-console/?email=<customer-email>`.
2. Check orders, payments, entitlements and webhook errors.
3. Confirm the purchased item type and target id from order items.
4. Check whether refund, chargeback, expiry or manual hold should block access.

## Repair
1. If payment/order is correct and entitlement is missing, use manual entitlement grant from support console.
2. If entitlement points to the wrong target, revoke the wrong entitlement first.
3. Grant the correct entitlement with a precise support reason.
4. Never bypass refund/chargeback holds without finance approval.

## Verification
- Support console shows the corrected entitlement.
- Content runtime opens the expected course/program/video.
- Audit contains grant/revoke operator, reason and target.

## Escalation
- Escalate to product/content ops if published content target ids changed unexpectedly.
- Escalate to finance if access is blocked by dispute/refund state.
