from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from typing import Any

from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.dateparse import parse_datetime


CRITICAL_STATUSES = {'critical'}
DEGRADED_STATUSES = {'degraded', 'critical'}


def _now():
    return timezone.now()


def _has_field(model: type, field_name: str) -> bool:
    return any(field.name == field_name for field in model._meta.get_fields())


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    if isinstance(value, str):
        parsed = parse_datetime(value)
        return parsed.isoformat() if parsed else value
    return str(value)


def _str_uuid(value: Any) -> str:
    return '' if value is None else str(value)


def _decimal(value: Any) -> str:
    if value is None:
        return '0.00'
    if isinstance(value, Decimal):
        return str(value.quantize(Decimal('0.01')))
    try:
        return str(Decimal(str(value)).quantize(Decimal('0.01')))
    except Exception:
        return str(value)


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


def _model_total_amount(queryset, field_name: str = 'amount') -> Decimal:
    return queryset.aggregate(total=Coalesce(Sum(field_name), Decimal('0.00')))['total'] or Decimal('0.00')


class AdminOperationsDashboardService:
    """Aggregates money-risk and async-infra health for the admin operations desk.

    This service intentionally reads from existing domain tables only. It does not
    create new operational state, so it is safe to ship without migrations and can
    be used by both the API and future admin frontend dashboards.
    """

    STUCK_MINUTES = 15
    RECENT_LIMIT = 10

    def snapshot(self) -> dict[str, Any]:
        generated_at = _now()
        outbox = self._outbox_section(generated_at=generated_at)
        webhooks = self._webhook_section(generated_at=generated_at)
        payments = self._payments_section()
        payouts = self._payouts_section()
        moderation = self._moderation_section()

        sections = [outbox, webhooks, payments, payouts, moderation]
        status = self._overall_status(sections)
        critical_items = []
        warning_items = []
        for section in sections:
            for issue in section.get('issues', []):
                if issue.get('severity') == 'critical':
                    critical_items.append(issue)
                else:
                    warning_items.append(issue)

        return {
            'status': status,
            'generated_at': generated_at,
            'sections': {
                'outbox': outbox,
                'webhooks': webhooks,
                'payments': payments,
                'payouts': payouts,
                'moderation': moderation,
            },
            'summary': {
                'critical_count': len(critical_items),
                'warning_count': len(warning_items),
                'critical_items': critical_items[: self.RECENT_LIMIT],
                'warning_items': warning_items[: self.RECENT_LIMIT],
            },
        }

    def _overall_status(self, sections: Iterable[dict[str, Any]]) -> str:
        statuses = {section.get('status', 'ok') for section in sections}
        if 'critical' in statuses:
            return 'critical'
        if 'degraded' in statuses:
            return 'degraded'
        return 'ok'

    def _outbox_section(self, *, generated_at) -> dict[str, Any]:
        from apps.events.models import OutboxMessage

        queryset = OutboxMessage.objects.all()
        stale_boundary = generated_at - timezone.timedelta(minutes=self.STUCK_MINUTES)
        failed_count = _safe_count(queryset.filter(status='failed'))
        dead_count = _safe_count(queryset.filter(status='dead'))
        pending_count = _safe_count(queryset.filter(status='pending'))
        processing_count = _safe_count(queryset.filter(status='processing'))
        stuck_processing = queryset.filter(status='processing')
        if _has_field(OutboxMessage, 'locked_at'):
            stuck_processing = stuck_processing.filter(locked_at__lt=stale_boundary)
        elif _has_field(OutboxMessage, 'updated_at'):
            stuck_processing = stuck_processing.filter(updated_at__lt=stale_boundary)
        stuck_processing_count = _safe_count(stuck_processing)

        issues = []
        if dead_count:
            issues.append({'code': 'outbox_dead_messages', 'severity': 'critical', 'count': dead_count})
        if failed_count:
            issues.append({'code': 'outbox_failed_messages', 'severity': 'critical', 'count': failed_count})
        if stuck_processing_count:
            issues.append({'code': 'outbox_stuck_processing', 'severity': 'warning', 'count': stuck_processing_count})
        if pending_count > 500:
            issues.append({'code': 'outbox_pending_backlog', 'severity': 'warning', 'count': pending_count})

        recent_failed = queryset.filter(status__in=['failed', 'dead']).select_related('event').order_by('-updated_at', '-created_at')[: self.RECENT_LIMIT]
        recent = []
        for message in recent_failed:
            event = getattr(message, 'event', None)
            recent.append({
                'id': _str_uuid(message.id),
                'status': message.status,
                'topic': getattr(message, 'topic', ''),
                'attempts': getattr(message, 'attempts', 0),
                'event_type': getattr(event, 'event_type', ''),
                'aggregate_type': getattr(event, 'aggregate_type', ''),
                'aggregate_id': getattr(event, 'aggregate_id', ''),
                'last_error': getattr(message, 'last_error', '')[:500],
                'updated_at': _iso(getattr(message, 'updated_at', None)),
            })

        status = 'critical' if failed_count or dead_count else 'degraded' if stuck_processing_count else 'ok'
        return {
            'status': status,
            'issues': issues,
            'counts': {
                'pending': pending_count,
                'processing': processing_count,
                'processed': _safe_count(queryset.filter(status='processed')),
                'failed': failed_count,
                'dead': dead_count,
                'stuck_processing': stuck_processing_count,
            },
            'by_status': _count_by(queryset, 'status'),
            'recent_problem_messages': recent,
        }

    def _webhook_section(self, *, generated_at) -> dict[str, Any]:
        from apps.payments.models import PaymentWebhookEvent

        queryset = PaymentWebhookEvent.objects.all()
        failed_count = _safe_count(queryset.filter(status='failed')) if _has_field(PaymentWebhookEvent, 'status') else 0
        rejected_count = _safe_count(queryset.filter(status='rejected')) if _has_field(PaymentWebhookEvent, 'status') else 0
        received_count = _safe_count(queryset.filter(status='received')) if _has_field(PaymentWebhookEvent, 'status') else 0
        processing_count = _safe_count(queryset.filter(status='processing')) if _has_field(PaymentWebhookEvent, 'status') else 0

        stale_boundary = generated_at - timezone.timedelta(minutes=self.STUCK_MINUTES)
        stuck_query = queryset.none()
        if _has_field(PaymentWebhookEvent, 'status'):
            stuck_query = queryset.filter(status__in=['received', 'processing'])
            if _has_field(PaymentWebhookEvent, 'received_at'):
                stuck_query = stuck_query.filter(received_at__lt=stale_boundary)
            elif _has_field(PaymentWebhookEvent, 'updated_at'):
                stuck_query = stuck_query.filter(updated_at__lt=stale_boundary)
        stuck_count = _safe_count(stuck_query)

        issues = []
        if failed_count:
            issues.append({'code': 'webhook_failed_events', 'severity': 'critical', 'count': failed_count})
        if rejected_count:
            issues.append({'code': 'webhook_rejected_events', 'severity': 'critical', 'count': rejected_count})
        if stuck_count:
            issues.append({'code': 'webhook_stuck_events', 'severity': 'warning', 'count': stuck_count})

        recent_query = queryset.order_by('-updated_at', '-created_at')
        if _has_field(PaymentWebhookEvent, 'status'):
            recent_query = recent_query.filter(status__in=['failed', 'rejected', 'received', 'processing'])
        recent = []
        for event in recent_query[: self.RECENT_LIMIT]:
            recent.append({
                'id': _str_uuid(event.id),
                'provider': getattr(event, 'provider', ''),
                'event_type': getattr(event, 'event_type', ''),
                'external_event_id': getattr(event, 'external_event_id', ''),
                'payment_id': _str_uuid(getattr(event, 'payment_id', '')),
                'status': getattr(event, 'status', 'processed' if getattr(event, 'processed_at', None) else 'received'),
                'error_message': getattr(event, 'error_message', '')[:500],
                'received_at': _iso(getattr(event, 'received_at', None) or getattr(event, 'created_at', None)),
                'processed_at': _iso(getattr(event, 'processed_at', None)),
            })

        status = 'critical' if failed_count or rejected_count else 'degraded' if stuck_count else 'ok'
        return {
            'status': status,
            'issues': issues,
            'counts': {
                'received': received_count,
                'processing': processing_count,
                'processed': _safe_count(queryset.filter(status='processed')) if _has_field(PaymentWebhookEvent, 'status') else _safe_count(queryset.filter(processed_at__isnull=False)),
                'duplicate': _safe_count(queryset.filter(status='duplicate')) if _has_field(PaymentWebhookEvent, 'status') else 0,
                'failed': failed_count,
                'rejected': rejected_count,
                'stuck': stuck_count,
            },
            'by_status': _count_by(queryset, 'status') if _has_field(PaymentWebhookEvent, 'status') else [],
            'recent_problem_events': recent,
        }

    def _payments_section(self) -> dict[str, Any]:
        from apps.payments.models import Payment

        queryset = Payment.objects.all()
        risk_statuses = ['disputed', 'charged_back', 'refunded', 'failed']
        disputed_count = _safe_count(queryset.filter(status='disputed'))
        chargeback_count = _safe_count(queryset.filter(status='charged_back'))
        refund_count = _safe_count(queryset.filter(status='refunded'))
        failed_count = _safe_count(queryset.filter(status='failed'))

        issues = []
        if chargeback_count:
            issues.append({'code': 'payments_charged_back', 'severity': 'critical', 'count': chargeback_count})
        if disputed_count:
            issues.append({'code': 'payments_disputed', 'severity': 'warning', 'count': disputed_count})
        if failed_count:
            issues.append({'code': 'payments_failed', 'severity': 'warning', 'count': failed_count})

        recent = []
        for payment in queryset.filter(status__in=risk_statuses).order_by('-updated_at')[: self.RECENT_LIMIT]:
            recent.append({
                'id': _str_uuid(payment.id),
                'status': payment.status,
                'amount': _decimal(getattr(payment, 'amount', None)),
                'currency': getattr(payment, 'currency', ''),
                'provider': getattr(payment, 'provider', ''),
                'external_payment_id': getattr(payment, 'external_payment_id', ''),
                'order_id': _str_uuid(getattr(payment, 'order_id', '')),
                'updated_at': _iso(getattr(payment, 'updated_at', None)),
            })

        status = 'critical' if chargeback_count else 'degraded' if disputed_count or failed_count else 'ok'
        return {
            'status': status,
            'issues': issues,
            'counts': {
                'disputed': disputed_count,
                'charged_back': chargeback_count,
                'refunded': refund_count,
                'failed': failed_count,
            },
            'by_status': _count_by(queryset, 'status'),
            'risk_amounts': {
                'disputed': _decimal(_model_total_amount(queryset.filter(status='disputed'))),
                'charged_back': _decimal(_model_total_amount(queryset.filter(status='charged_back'))),
                'refunded': _decimal(_model_total_amount(queryset.filter(status='refunded'))),
            },
            'recent_risk_payments': recent,
        }

    def _payouts_section(self) -> dict[str, Any]:
        from apps.payouts.models import BalanceEntry, PayoutRequest, TrainerWallet

        wallets = TrainerWallet.objects.all()
        entries = BalanceEntry.objects.all()
        payout_requests = PayoutRequest.objects.all()
        locked_total = wallets.aggregate(total=Coalesce(Sum('locked_amount'), Decimal('0.00')))['total'] or Decimal('0.00')
        pending_payout_count = _safe_count(payout_requests.filter(status__in=['requested', 'pending', 'approved', 'processing']))
        risk_hold_count = _safe_count(entries.filter(entry_type__in=['risk_hold', 'risk_hold_release', 'risk_hold_consumed']))
        active_hold_count = _safe_count(entries.filter(entry_type='risk_hold'))
        reversal_count = _safe_count(entries.filter(entry_type='reversal'))

        issues = []
        if locked_total > Decimal('0.00'):
            issues.append({'code': 'payout_locked_risk_amount', 'severity': 'warning', 'amount': _decimal(locked_total)})
        if pending_payout_count > 50:
            issues.append({'code': 'payout_pending_backlog', 'severity': 'warning', 'count': pending_payout_count})

        recent_holds = []
        for entry in entries.filter(entry_type__in=['risk_hold', 'risk_hold_release', 'risk_hold_consumed', 'reversal']).select_related('wallet').order_by('-created_at')[: self.RECENT_LIMIT]:
            recent_holds.append({
                'id': _str_uuid(entry.id),
                'entry_type': getattr(entry, 'entry_type', ''),
                'direction': getattr(entry, 'direction', ''),
                'amount': _decimal(getattr(entry, 'amount', None)),
                'currency': getattr(entry, 'currency', ''),
                'source_type': getattr(entry, 'source_type', ''),
                'source_id': _str_uuid(getattr(entry, 'source_id', '')),
                'trainer_id': _str_uuid(getattr(entry, 'trainer_id', '')),
                'created_at': _iso(getattr(entry, 'created_at', None)),
            })

        return {
            'status': 'degraded' if issues else 'ok',
            'issues': issues,
            'counts': {
                'wallets': _safe_count(wallets),
                'pending_payout_requests': pending_payout_count,
                'risk_hold_entries': risk_hold_count,
                'active_hold_entries': active_hold_count,
                'reversal_entries': reversal_count,
            },
            'amounts': {
                'locked_total': _decimal(locked_total),
                'available_total': _decimal(wallets.aggregate(total=Coalesce(Sum('available_amount'), Decimal('0.00')))['total'] or Decimal('0.00')),
                'pending_total': _decimal(wallets.aggregate(total=Coalesce(Sum('pending_amount'), Decimal('0.00')))['total'] or Decimal('0.00')),
            },
            'payout_request_by_status': _count_by(payout_requests, 'status'),
            'recent_risk_ledger_entries': recent_holds,
        }

    def _moderation_section(self) -> dict[str, Any]:
        from apps.moderation.models import ModerationCase, TrainerRiskFlag

        cases = ModerationCase.objects.all()
        risk_cases = cases.filter(queue='payments_risk')
        open_risk_cases = risk_cases.exclude(status='resolved')
        flags = TrainerRiskFlag.objects.all()
        active_flags = flags.filter(is_active=True)
        active_payment_flags = active_flags.filter(code__in=['payment_dispute_opened', 'payment_chargeback_lost'])

        issues = []
        active_critical_flags = _safe_count(active_payment_flags.filter(risk_level='critical'))
        active_high_flags = _safe_count(active_payment_flags.filter(risk_level='high'))
        if active_critical_flags:
            issues.append({'code': 'critical_payment_risk_flags', 'severity': 'critical', 'count': active_critical_flags})
        if active_high_flags:
            issues.append({'code': 'high_payment_risk_flags', 'severity': 'warning', 'count': active_high_flags})
        open_count = _safe_count(open_risk_cases)
        if open_count:
            issues.append({'code': 'open_payment_risk_cases', 'severity': 'warning', 'count': open_count})

        recent_cases = []
        for case in risk_cases.select_related('trainer').order_by('-updated_at')[: self.RECENT_LIMIT]:
            recent_cases.append({
                'id': _str_uuid(case.id),
                'status': getattr(case, 'status', ''),
                'priority': getattr(case, 'priority', None),
                'target_type': getattr(case, 'target_type', ''),
                'target_id': getattr(case, 'target_id', ''),
                'title': getattr(case, 'title', ''),
                'trainer_id': _str_uuid(getattr(case, 'trainer_id', '')),
                'updated_at': _iso(getattr(case, 'updated_at', None)),
            })

        status = 'critical' if active_critical_flags else 'degraded' if issues else 'ok'
        return {
            'status': status,
            'issues': issues,
            'counts': {
                'payment_risk_cases': _safe_count(risk_cases),
                'open_payment_risk_cases': open_count,
                'active_payment_risk_flags': _safe_count(active_payment_flags),
                'active_critical_flags': active_critical_flags,
                'active_high_flags': active_high_flags,
            },
            'case_by_status': _count_by(risk_cases, 'status'),
            'flag_by_level': _count_by(active_payment_flags, 'risk_level'),
            'recent_payment_risk_cases': recent_cases,
        }


def get_admin_operations_dashboard() -> dict[str, Any]:
    return AdminOperationsDashboardService().snapshot()
