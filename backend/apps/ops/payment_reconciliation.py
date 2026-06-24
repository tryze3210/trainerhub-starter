from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

from django.utils import timezone


PROVIDER_SUCCESS_EVENTS = {'payment.succeeded', 'payment.paid', 'payment.captured', 'checkout.paid'}
PROVIDER_REFUND_EVENTS = {'payment.refunded', 'payment.refund.succeeded', 'refund.succeeded', 'checkout.refunded'}
PROCESSED_WEBHOOK_STATUS = 'processed'
SUCCESS_PAYMENT_STATUS = 'succeeded'
REFUNDED_PAYMENT_STATUS = 'refunded'


@dataclass(frozen=True)
class PaymentReconciliationIssue:
    code: str
    severity: str
    entity_type: str
    entity_id: str
    message: str
    suggested_action: str
    related: list[dict[str, str]]
    evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return _jsonify(asdict(self))


def _jsonify(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return str(value.quantize(Decimal('0.01')))
    if isinstance(value, UUID):
        return str(value)
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _jsonify(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonify(item) for item in value]
    return value


def _rel(entity_type: str, entity_id: Any, label: str) -> dict[str, str] | None:
    if entity_id in {None, ''}:
        return None
    return {
        'entity_type': entity_type,
        'entity_id': str(entity_id),
        'label': label,
        'href': f'/admin/entities/{entity_type}/{entity_id}',
    }


def _rels(*items: dict[str, str] | None) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    result: list[dict[str, str]] = []
    for item in items:
        if not item:
            continue
        key = (item['entity_type'], item['entity_id'])
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _issue(
    *,
    code: str,
    severity: str,
    entity_type: str,
    entity_id: Any,
    message: str,
    suggested_action: str,
    related: list[dict[str, str] | None] | None = None,
    evidence: dict[str, Any] | None = None,
) -> PaymentReconciliationIssue:
    return PaymentReconciliationIssue(
        code=code,
        severity=severity,
        entity_type=entity_type,
        entity_id=str(entity_id),
        message=message,
        suggested_action=suggested_action,
        related=_rels(*(related or [])),
        evidence=evidence or {},
    )


def _external_payment_id(payload: dict | None) -> str:
    payload = payload or {}
    return str(
        payload.get('external_payment_id')
        or payload.get('provider_payment_id')
        or payload.get('payment_id')
        or payload.get('InvoiceId')
        or payload.get('invoice_id')
        or ''
    )


class PaymentReconciliationService:
    """Payment-focused reconciliation across provider webhooks, internal state and access grants."""

    def report(self, *, limit: int = 100) -> dict[str, Any]:
        from apps.entitlements.models import Entitlement
        from apps.payments.models import Payment, PaymentWebhookEvent

        limit = max(1, min(int(limit or 100), 500))
        generated_at = timezone.now()
        issues: list[PaymentReconciliationIssue] = []

        payments = Payment.objects.select_related('order').all()
        webhooks = PaymentWebhookEvent.objects.select_related('payment').all()
        success_webhooks = webhooks.filter(status=PROCESSED_WEBHOOK_STATUS, event_type__in=PROVIDER_SUCCESS_EVENTS)
        refund_webhooks = webhooks.filter(status=PROCESSED_WEBHOOK_STATUS, event_type__in=PROVIDER_REFUND_EVENTS)

        provider_success_count = success_webhooks.count()
        provider_refund_count = refund_webhooks.count()
        internal_success_count = payments.filter(status=SUCCESS_PAYMENT_STATUS).count()
        internal_refunded_count = payments.filter(status=REFUNDED_PAYMENT_STATUS).count()
        active_entitlement_count = Entitlement.objects.filter(status='active').count()

        for event in success_webhooks.order_by('-received_at')[:limit]:
            external_id = _external_payment_id(event.payload)
            payment = event.payment or payments.filter(external_payment_id=external_id).first()
            if not payment:
                issues.append(_issue(
                    code='provider_success_without_internal_payment',
                    severity='critical',
                    entity_type='payment_webhook',
                    entity_id=event.id,
                    message='Provider reported a successful payment, but no internal payment matches it.',
                    suggested_action='Inspect provider identifiers, then attach or create the internal payment record before granting access.',
                    related=[],
                    evidence={'provider': event.provider, 'external_event_id': event.external_event_id, 'external_payment_id': external_id},
                ))
                continue
            if payment.status != SUCCESS_PAYMENT_STATUS:
                issues.append(_issue(
                    code='provider_success_internal_not_succeeded',
                    severity='critical',
                    entity_type='payment',
                    entity_id=payment.id,
                    message='Provider reported success, but internal payment is not succeeded.',
                    suggested_action='Reprocess the webhook or reconcile payment status before granting/revoking access.',
                    related=[_rel('payment_webhook', event.id, 'Provider success webhook'), _rel('order', payment.order_id, 'Order')],
                    evidence={
                        'provider': event.provider,
                        'external_event_id': event.external_event_id,
                        'external_payment_id': external_id,
                        'payment_status': payment.status,
                        'order_status': payment.order.status,
                    },
                ))

        for payment in payments.filter(status=SUCCESS_PAYMENT_STATUS).order_by('-confirmed_at', '-created_at')[:limit]:
            access_count = self._access_count_for_payment(payment)
            if access_count == 0:
                issues.append(_issue(
                    code='internal_success_without_entitlement',
                    severity='critical',
                    entity_type='payment',
                    entity_id=payment.id,
                    message='Internal payment is succeeded, but no active entitlement or subscription access was found.',
                    suggested_action='Run payment success reconciliation or grant order access through the audited repair flow.',
                    related=[_rel('order', payment.order_id, 'Order')],
                    evidence={
                        'payment_status': payment.status,
                        'order_status': payment.order.status,
                        'external_payment_id': payment.external_payment_id,
                    },
                ))

        for event in refund_webhooks.order_by('-received_at')[:limit]:
            external_id = _external_payment_id(event.payload)
            payment = event.payment or payments.filter(external_payment_id=external_id).first()
            if not payment:
                issues.append(_issue(
                    code='provider_refund_without_internal_payment',
                    severity='critical',
                    entity_type='payment_webhook',
                    entity_id=event.id,
                    message='Provider reported a refund, but no internal payment matches it.',
                    suggested_action='Inspect provider identifiers and reconcile the missing internal payment before closing the refund.',
                    related=[],
                    evidence={'provider': event.provider, 'external_event_id': event.external_event_id, 'external_payment_id': external_id},
                ))
                continue
            payload = payment.provider_payload or {}
            if payment.status != REFUNDED_PAYMENT_STATUS and not payload.get('refund_operations'):
                issues.append(_issue(
                    code='provider_refund_internal_not_refunded',
                    severity='critical',
                    entity_type='payment',
                    entity_id=payment.id,
                    message='Provider reported a refund, but internal payment has no refund operation.',
                    suggested_action='Reprocess the refund webhook or run the refund flow with the provider refund id.',
                    related=[_rel('payment_webhook', event.id, 'Provider refund webhook'), _rel('order', payment.order_id, 'Order')],
                    evidence={
                        'provider': event.provider,
                        'external_event_id': event.external_event_id,
                        'external_payment_id': external_id,
                        'payment_status': payment.status,
                        'refund_status': payload.get('refund_status', ''),
                    },
                ))

        for payment in payments.filter(status=REFUNDED_PAYMENT_STATUS).order_by('-updated_at')[:limit]:
            active_access_count = self._access_count_for_payment(payment)
            if active_access_count:
                issues.append(_issue(
                    code='internal_refund_has_active_entitlement',
                    severity='critical',
                    entity_type='payment',
                    entity_id=payment.id,
                    message='Internal payment is refunded, but active access still exists.',
                    suggested_action='Run entitlement revoke for the payment order and verify subscription cancellation.',
                    related=[_rel('order', payment.order_id, 'Order')],
                    evidence={
                        'payment_status': payment.status,
                        'order_status': payment.order.status,
                        'active_access_count': active_access_count,
                        'refund_status': (payment.provider_payload or {}).get('refund_status', ''),
                    },
                ))

        issue_counts: dict[str, int] = defaultdict(int)
        for issue in issues:
            issue_counts[issue.severity] += 1

        status = 'critical' if issue_counts.get('critical') else 'degraded' if issues else 'ok'
        return {
            'status': status,
            'generated_at': generated_at,
            'summary': {
                'total_issues': len(issues),
                'critical_count': issue_counts.get('critical', 0),
                'warning_count': issue_counts.get('warning', 0),
                'by_severity': dict(sorted(issue_counts.items())),
            },
            'metrics': _jsonify({
                'provider_payments': {
                    'successful_webhook_count': provider_success_count,
                    'refund_webhook_count': provider_refund_count,
                },
                'internal_payments': {
                    'succeeded_count': internal_success_count,
                    'refunded_count': internal_refunded_count,
                    'total_count': payments.count(),
                },
                'entitlements': {
                    'active_count': active_entitlement_count,
                },
            }),
            'checks': [
                {'code': 'provider_success_without_internal_payment', 'description': 'Provider success must map to an internal payment.'},
                {'code': 'provider_success_internal_not_succeeded', 'description': 'Provider success must result in internal succeeded status.'},
                {'code': 'internal_success_without_entitlement', 'description': 'Succeeded internal payment must activate entitlement or subscription access.'},
                {'code': 'provider_refund_without_internal_payment', 'description': 'Provider refund must map to an internal payment.'},
                {'code': 'provider_refund_internal_not_refunded', 'description': 'Provider refund must create an internal refund operation.'},
                {'code': 'internal_refund_has_active_entitlement', 'description': 'Full internal refund must leave no active access.'},
            ],
            'issues': [issue.to_dict() for issue in issues[:limit]],
        }

    @staticmethod
    def _access_count_for_payment(payment) -> int:
        from apps.entitlements.models import Entitlement

        order = payment.order
        direct_count = Entitlement.objects.filter(source_order=order, status='active').count()
        subscription_count = Entitlement.objects.filter(source_subscription__source_order=order, status='active').count()
        return direct_count + subscription_count


def get_payment_reconciliation_report(*, limit: int = 100) -> dict[str, Any]:
    return PaymentReconciliationService().report(limit=limit)
