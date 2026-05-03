from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import timedelta
from decimal import Decimal
from typing import Any, Iterable
from uuid import UUID

from django.db.models import Count, Q
from django.utils import timezone


PAID_ORDER_STATUSES = {'paid', 'completed'}
SUCCESS_PAYMENT_STATUSES = {'succeeded'}
RISK_PAYMENT_STATUSES = {'refunded', 'disputed', 'charged_back', 'failed'}
OPEN_WEBHOOK_STATUSES = {'received', 'processing'}
BAD_WEBHOOK_STATUSES = {'failed', 'rejected'}
BAD_OUTBOX_STATUSES = {'failed', 'dead'}


@dataclass(frozen=True)
class ReconciliationIssue:
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


def _now():
    return timezone.now()


def _has_field(model: type, field_name: str) -> bool:
    return any(field.name == field_name for field in model._meta.get_fields())


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
    related: Iterable[dict[str, str] | None] = (),
    evidence: dict[str, Any] | None = None,
) -> ReconciliationIssue:
    return ReconciliationIssue(
        code=code,
        severity=severity,
        entity_type=entity_type,
        entity_id=str(entity_id),
        message=message,
        suggested_action=suggested_action,
        related=_rels(*related),
        evidence=evidence or {},
    )


def _count_by(queryset, field_name: str) -> list[dict[str, Any]]:
    return [
        {'key': item[field_name] or 'unknown', 'count': item['count']}
        for item in queryset.values(field_name).annotate(count=Count('id')).order_by(field_name)
    ]


def _safe_count(queryset) -> int:
    try:
        return int(queryset.count())
    except Exception:
        return 0


class MoneyReconciliationService:
    """Cross-checks money, access and async infrastructure consistency.

    This report is intentionally read-only. It does not repair data. The admin
    operations desk should use it to find mismatches and then route fixes through
    audited actions such as webhook reprocess, outbox retry, payout reversal or
    manual entitlement review.
    """

    RECENT_LIMIT = 25
    STUCK_MINUTES = 15

    def report(self, *, limit: int = 100) -> dict[str, Any]:
        limit = max(1, min(int(limit or self.RECENT_LIMIT), 500))
        generated_at = _now()
        sections = {
            'payments': self._payment_issues(limit=limit),
            'orders': self._order_issues(limit=limit),
            'entitlements': self._entitlement_issues(limit=limit),
            'payouts': self._payout_issues(limit=limit),
            'webhooks': self._webhook_issues(limit=limit, generated_at=generated_at),
            'outbox': self._outbox_issues(limit=limit, generated_at=generated_at),
        }

        issue_counts: dict[str, int] = defaultdict(int)
        for section in sections.values():
            for issue in section['issues']:
                issue_counts[issue['severity']] += 1

        status = 'critical' if issue_counts.get('critical') else 'degraded' if issue_counts else 'ok'
        return {
            'status': status,
            'generated_at': generated_at,
            'summary': {
                'total_issues': sum(issue_counts.values()),
                'critical_count': issue_counts.get('critical', 0),
                'warning_count': issue_counts.get('warning', 0),
                'info_count': issue_counts.get('info', 0),
                'by_severity': dict(sorted(issue_counts.items())),
            },
            'sections': sections,
        }

    def _section(self, *, status: str, checks: list[dict[str, Any]], issues: list[ReconciliationIssue], metrics: dict[str, Any] | None = None) -> dict[str, Any]:
        serialized = [issue.to_dict() for issue in issues]
        if any(issue['severity'] == 'critical' for issue in serialized):
            status = 'critical'
        elif serialized and status == 'ok':
            status = 'degraded'
        return {
            'status': status,
            'metrics': _jsonify(metrics or {}),
            'checks': checks,
            'issue_count': len(serialized),
            'issues': serialized,
        }

    def _payment_issues(self, *, limit: int) -> dict[str, Any]:
        from apps.entitlements.models import Entitlement
        from apps.orders.models import Order
        from apps.payments.models import Payment

        issues: list[ReconciliationIssue] = []
        payments = Payment.objects.select_related('order').all()

        successful_with_bad_order = payments.filter(status__in=SUCCESS_PAYMENT_STATUSES).exclude(order__status__in=PAID_ORDER_STATUSES)[:limit]
        for payment in successful_with_bad_order:
            order = payment.order
            issues.append(_issue(
                code='payment_succeeded_order_not_paid',
                severity='critical',
                entity_type='payment',
                entity_id=payment.id,
                message='Payment is succeeded, but related order is not paid or completed.',
                suggested_action='Open the payment and order, then re-run the payment lifecycle or review the webhook processing trail.',
                related=[_rel('order', order.id, 'Order')],
                evidence={
                    'payment_status': payment.status,
                    'order_status': order.status,
                    'amount': payment.amount,
                    'currency': payment.currency,
                    'external_payment_id': payment.external_payment_id,
                },
            ))

        risk_with_active_entitlements = payments.filter(status__in={'refunded', 'charged_back'}).filter(order__granted_entitlements__status='active').distinct()[:limit]
        for payment in risk_with_active_entitlements:
            active_count = Entitlement.objects.filter(source_order=payment.order, status='active').count()
            issues.append(_issue(
                code='risk_payment_has_active_entitlement',
                severity='critical',
                entity_type='payment',
                entity_id=payment.id,
                message='Refunded or charged-back payment still has active access grants.',
                suggested_action='Open related entitlements and revoke access through the refund/chargeback lifecycle.',
                related=[_rel('order', payment.order_id, 'Order')],
                evidence={'payment_status': payment.status, 'active_entitlement_count': active_count},
            ))

        return self._section(
            status='ok',
            metrics={
                'by_status': _count_by(payments, 'status'),
                'successful_payments': _safe_count(payments.filter(status__in=SUCCESS_PAYMENT_STATUSES)),
                'risk_payments': _safe_count(payments.filter(status__in=RISK_PAYMENT_STATUSES)),
            },
            checks=[
                {'code': 'payment_succeeded_order_not_paid', 'description': 'Succeeded payment must have a paid/completed order.'},
                {'code': 'risk_payment_has_active_entitlement', 'description': 'Refunded/charged-back payment must not leave active entitlements.'},
            ],
            issues=issues,
        )

    def _order_issues(self, *, limit: int) -> dict[str, Any]:
        from apps.orders.models import Order

        issues: list[ReconciliationIssue] = []
        orders = Order.objects.all()

        paid_without_success_payment = orders.filter(status__in=PAID_ORDER_STATUSES).exclude(payments__status__in=SUCCESS_PAYMENT_STATUSES).distinct()[:limit]
        for order in paid_without_success_payment:
            issues.append(_issue(
                code='paid_order_without_successful_payment',
                severity='critical',
                entity_type='order',
                entity_id=order.id,
                message='Order is paid/completed, but no succeeded payment exists for it.',
                suggested_action='Inspect payment webhooks for this order and reconcile the payment status.',
                related=[],
                evidence={'order_status': order.status, 'total_amount': order.total_amount, 'currency': order.currency},
            ))

        completed_without_entitlement = orders.filter(status='completed').exclude(granted_entitlements__status='active').distinct()[:limit]
        for order in completed_without_entitlement:
            issues.append(_issue(
                code='completed_order_without_active_entitlement',
                severity='critical',
                entity_type='order',
                entity_id=order.id,
                message='Completed order has no active entitlement.',
                suggested_action='Run or re-run the order completion/access grant workflow for this order.',
                related=[],
                evidence={'order_status': order.status, 'total_amount': order.total_amount, 'currency': order.currency},
            ))

        return self._section(
            status='ok',
            metrics={
                'by_status': _count_by(orders, 'status'),
                'paid_or_completed_orders': _safe_count(orders.filter(status__in=PAID_ORDER_STATUSES)),
            },
            checks=[
                {'code': 'paid_order_without_successful_payment', 'description': 'Paid/completed orders should have a succeeded payment.'},
                {'code': 'completed_order_without_active_entitlement', 'description': 'Completed orders should grant active access.'},
            ],
            issues=issues,
        )

    def _entitlement_issues(self, *, limit: int) -> dict[str, Any]:
        from apps.entitlements.models import Entitlement

        issues: list[ReconciliationIssue] = []
        entitlements = Entitlement.objects.all()

        active_from_bad_order = entitlements.filter(status='active', source_order__isnull=False).exclude(source_order__status__in=PAID_ORDER_STATUSES)[:limit]
        for entitlement in active_from_bad_order:
            issues.append(_issue(
                code='active_entitlement_from_unpaid_order',
                severity='critical',
                entity_type='entitlement',
                entity_id=entitlement.id,
                message='Active entitlement references an order that is not paid/completed.',
                suggested_action='Review the order and revoke or regenerate entitlement through the payment lifecycle.',
                related=[_rel('order', entitlement.source_order_id, 'Source order')],
                evidence={
                    'entitlement_status': entitlement.status,
                    'source_order_status': getattr(entitlement.source_order, 'status', ''),
                    'target_type': entitlement.target_type,
                    'target_id': entitlement.target_id,
                },
            ))

        active_from_bad_subscription = entitlements.filter(status='active', source_subscription__isnull=False).exclude(source_subscription__status='active')[:limit]
        for entitlement in active_from_bad_subscription:
            issues.append(_issue(
                code='active_entitlement_from_inactive_subscription',
                severity='warning',
                entity_type='entitlement',
                entity_id=entitlement.id,
                message='Active entitlement references a subscription that is not active.',
                suggested_action='Review subscription lifecycle and expire or revoke entitlement if the subscription is no longer active.',
                related=[_rel('subscription', entitlement.source_subscription_id, 'Source subscription')],
                evidence={
                    'entitlement_status': entitlement.status,
                    'source_subscription_status': getattr(entitlement.source_subscription, 'status', ''),
                    'target_type': entitlement.target_type,
                    'target_id': entitlement.target_id,
                },
            ))

        return self._section(
            status='ok',
            metrics={'by_status': _count_by(entitlements, 'status'), 'active_entitlements': _safe_count(entitlements.filter(status='active'))},
            checks=[
                {'code': 'active_entitlement_from_unpaid_order', 'description': 'Active order-based access must be backed by a paid/completed order.'},
                {'code': 'active_entitlement_from_inactive_subscription', 'description': 'Active subscription-based access must be backed by an active subscription.'},
            ],
            issues=issues,
        )

    def _payout_issues(self, *, limit: int) -> dict[str, Any]:
        from apps.payments.models import Payment
        from apps.payouts.models import PayoutLedgerEntry, TrainerBalance

        issues: list[ReconciliationIssue] = []
        ledger = PayoutLedgerEntry.objects.select_related('wallet', 'wallet__trainer').all()

        payment_accruals = ledger.filter(entry_type='accrual', source_type='payment')[:limit]
        for entry in payment_accruals:
            payment = Payment.objects.filter(id=entry.source_id).select_related('order').first()
            if not payment:
                issues.append(_issue(
                    code='payout_accrual_missing_payment',
                    severity='critical',
                    entity_type='payout_ledger',
                    entity_id=entry.id,
                    message='Payout accrual references a missing payment.',
                    suggested_action='Review ledger entry and reverse or repair it through payout reconciliation.',
                    related=[],
                    evidence={'source_type': entry.source_type, 'source_id': entry.source_id, 'amount': entry.amount, 'direction': entry.direction},
                ))
                continue
            if payment.status not in SUCCESS_PAYMENT_STATUSES:
                issues.append(_issue(
                    code='payout_accrual_for_non_success_payment',
                    severity='critical',
                    entity_type='payout_ledger',
                    entity_id=entry.id,
                    message='Payout accrual references a payment that is not succeeded.',
                    suggested_action='Open payment and ledger entry; reverse accrual if payment is refunded, charged back or failed.',
                    related=[_rel('payment', payment.id, 'Payment'), _rel('order', payment.order_id, 'Order')],
                    evidence={'payment_status': payment.status, 'entry_amount': entry.amount, 'entry_direction': entry.direction},
                ))

        succeeded_without_accrual = Payment.objects.filter(status__in=SUCCESS_PAYMENT_STATUSES).exclude(id__in=ledger.filter(entry_type='accrual', source_type='payment').values('source_id'))[:limit]
        for payment in succeeded_without_accrual:
            issues.append(_issue(
                code='succeeded_payment_without_payout_accrual',
                severity='warning',
                entity_type='payment',
                entity_id=payment.id,
                message='Succeeded payment has no payout accrual ledger entry.',
                suggested_action='Confirm whether this payment is commission-only/test data; otherwise run payout revenue projection.',
                related=[_rel('order', payment.order_id, 'Order')],
                evidence={'payment_status': payment.status, 'amount': payment.amount, 'currency': payment.currency},
            ))

        return self._section(
            status='ok',
            metrics={
                'wallet_count': _safe_count(TrainerBalance.objects.all()),
                'ledger_by_entry_type': _count_by(ledger, 'entry_type'),
                'ledger_by_source_type': _count_by(ledger, 'source_type'),
            },
            checks=[
                {'code': 'payout_accrual_missing_payment', 'description': 'Every payment accrual must reference an existing payment.'},
                {'code': 'payout_accrual_for_non_success_payment', 'description': 'Payment accruals must only exist for succeeded payments.'},
                {'code': 'succeeded_payment_without_payout_accrual', 'description': 'Succeeded trainer payments should project to payout accruals.'},
            ],
            issues=issues,
        )

    def _webhook_issues(self, *, limit: int, generated_at) -> dict[str, Any]:
        from apps.payments.models import PaymentWebhookEvent

        issues: list[ReconciliationIssue] = []
        webhooks = PaymentWebhookEvent.objects.all()
        stale_boundary = generated_at - timedelta(minutes=self.STUCK_MINUTES)
        problem_filter = Q(status__in=BAD_WEBHOOK_STATUSES) | Q(status='processing', received_at__lt=stale_boundary) | Q(status='received', received_at__lt=stale_boundary)
        for event in webhooks.filter(problem_filter).order_by('-received_at')[:limit]:
            severity = 'critical' if event.status in BAD_WEBHOOK_STATUSES else 'warning'
            issues.append(_issue(
                code='payment_webhook_problem',
                severity=severity,
                entity_type='payment_webhook',
                entity_id=event.id,
                message='Payment webhook is failed, rejected or stuck before processing.',
                suggested_action='Open webhook detail and reprocess if safe; verify signature/provider payload before forcing.',
                related=[_rel('payment', event.payment_id, 'Payment')],
                evidence={
                    'status': event.status,
                    'provider': event.provider,
                    'event_type': event.event_type,
                    'external_event_id': event.external_event_id,
                    'attempts': getattr(event, 'attempts', 0),
                    'error_message': getattr(event, 'error_message', ''),
                    'received_at': event.received_at,
                    'processed_at': event.processed_at,
                },
            ))

        return self._section(
            status='ok',
            metrics={'by_status': _count_by(webhooks, 'status'), 'total_webhooks': _safe_count(webhooks)},
            checks=[{'code': 'payment_webhook_problem', 'description': 'Webhooks should not remain failed, rejected, received or processing for too long.'}],
            issues=issues,
        )

    def _outbox_issues(self, *, limit: int, generated_at) -> dict[str, Any]:
        from apps.events.models import OutboxMessage

        issues: list[ReconciliationIssue] = []
        outbox = OutboxMessage.objects.select_related('event').all()
        stale_boundary = generated_at - timedelta(minutes=self.STUCK_MINUTES)
        processing = outbox.filter(status='processing')
        if _has_field(OutboxMessage, 'locked_at'):
            processing = processing.filter(locked_at__lt=stale_boundary)
        else:
            processing = processing.filter(updated_at__lt=stale_boundary)

        problem_queryset = (outbox.filter(status__in=BAD_OUTBOX_STATUSES) | processing).order_by('-updated_at', '-created_at')[:limit]
        for message in problem_queryset:
            event = getattr(message, 'event', None)
            severity = 'critical' if message.status in BAD_OUTBOX_STATUSES else 'warning'
            issues.append(_issue(
                code='outbox_delivery_problem',
                severity=severity,
                entity_type='outbox_message',
                entity_id=message.id,
                message='Outbox message failed, is dead, or is stuck in processing.',
                suggested_action='Open outbox detail, inspect last_error, then retry, mark dead or requeue stuck messages.',
                related=[
                    _rel('domain_event', getattr(event, 'id', None), 'Domain event'),
                    _rel(str(getattr(event, 'aggregate_type', '') or ''), getattr(event, 'aggregate_id', ''), 'Aggregate'),
                ],
                evidence={
                    'status': message.status,
                    'topic': getattr(message, 'topic', ''),
                    'attempts': getattr(message, 'attempts', 0),
                    'max_attempts': getattr(message, 'max_attempts', 0),
                    'last_error': getattr(message, 'last_error', ''),
                    'event_type': getattr(event, 'event_type', ''),
                    'aggregate_type': getattr(event, 'aggregate_type', ''),
                    'aggregate_id': getattr(event, 'aggregate_id', ''),
                },
            ))

        return self._section(
            status='ok',
            metrics={'by_status': _count_by(outbox, 'status'), 'total_outbox_messages': _safe_count(outbox)},
            checks=[{'code': 'outbox_delivery_problem', 'description': 'Outbox messages should not be failed, dead or stuck processing.'}],
            issues=issues,
        )


def get_money_reconciliation_report(*, limit: int = 100) -> dict[str, Any]:
    return MoneyReconciliationService().report(limit=limit)
