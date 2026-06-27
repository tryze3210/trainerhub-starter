from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.db.models import Count
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.events.models import InboxMessage, OutboxMessage
from apps.payments.models import Payment, PaymentStatus, PaymentWebhookEvent


def _rate(*, numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def _status_for_rate(rate: float, *, warning: float, critical: float) -> str:
    if rate >= critical:
        return "critical"
    if rate >= warning:
        return "degraded"
    return "healthy"


def _status_for_count(count: int, *, warning: int, critical: int) -> str:
    if count >= critical:
        return "critical"
    if count >= warning:
        return "degraded"
    return "healthy"


def _worst_status(*statuses: str) -> str:
    rank = {"healthy": 0, "ok": 0, "degraded": 1, "warning": 1, "critical": 2}
    if not statuses:
        return "healthy"
    return sorted(statuses, key=lambda item: rank.get(item, 1), reverse=True)[0]


class ObservabilityRuntimeService:
    """Production runtime health snapshot built from durable operational tables."""

    DEFAULT_WINDOW_HOURS = 24

    @staticmethod
    def _alert(*, code: str, severity: str, title: str, detail: str, value: Any = None) -> dict[str, Any]:
        return {
            "code": code,
            "severity": severity,
            "title": title,
            "detail": detail,
            "value": value,
        }

    @classmethod
    def _webhook_health(cls, *, since) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        queryset = PaymentWebhookEvent.objects.filter(received_at__gte=since)
        total = queryset.count()
        failed = queryset.filter(status__in=[PaymentWebhookEvent.Status.FAILED, PaymentWebhookEvent.Status.REJECTED]).count()
        processing = queryset.filter(status__in=[PaymentWebhookEvent.Status.RECEIVED, PaymentWebhookEvent.Status.PROCESSING]).count()
        failure_rate = _rate(numerator=failed, denominator=total)
        status = _status_for_rate(failure_rate, warning=2.0, critical=10.0)
        if processing >= 25:
            status = _worst_status(status, "degraded")
        by_status = list(queryset.values("status").annotate(count=Count("id")).order_by("status"))
        alerts = []
        if failed:
            alerts.append(cls._alert(code="webhook_failures", severity=status, title="Webhook failures detected", detail="Payment webhook failures or rejections exist in the active window.", value=failed))
        if processing >= 25:
            alerts.append(cls._alert(code="webhook_backlog", severity="degraded", title="Webhook backlog detected", detail="Webhook events are still received/processing.", value=processing))
        return {
            "status": status,
            "window_hours": cls.DEFAULT_WINDOW_HOURS,
            "total": total,
            "failed": failed,
            "processing": processing,
            "failure_rate": failure_rate,
            "by_status": by_status,
        }, alerts

    @classmethod
    def _payment_health(cls, *, since) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        queryset = Payment.objects.filter(created_at__gte=since)
        total = queryset.count()
        failed = queryset.filter(status__in=[PaymentStatus.FAILED, PaymentStatus.CANCELLED, PaymentStatus.CHARGED_BACK]).count()
        disputed = queryset.filter(status=PaymentStatus.DISPUTED).count()
        error_rate = _rate(numerator=failed, denominator=total)
        status = _status_for_rate(error_rate, warning=5.0, critical=15.0)
        if disputed:
            status = _worst_status(status, "degraded")
        by_status = list(queryset.values("status").annotate(count=Count("id")).order_by("status"))
        alerts = []
        if failed:
            alerts.append(cls._alert(code="payment_errors", severity=status, title="Payment error rate is non-zero", detail="Failed, cancelled or charged-back payments exist in the active window.", value=failed))
        if disputed:
            alerts.append(cls._alert(code="payment_disputes", severity="degraded", title="Open disputed payments", detail="Disputed payments require finance/support monitoring.", value=disputed))
        return {
            "status": status,
            "window_hours": cls.DEFAULT_WINDOW_HOURS,
            "total": total,
            "failed": failed,
            "disputed": disputed,
            "error_rate": error_rate,
            "by_status": by_status,
        }, alerts

    @classmethod
    def _payout_repair_health(cls, *, since) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        queryset = AuditEvent.objects.filter(
            created_at__gte=since,
            event_type="admin.payouts.repair_execution",
            entity_type="payout_repair_execution",
        )
        total_runs = queryset.count()
        repaired = 0
        manual_review = 0
        for event in queryset:
            context = event.context or {}
            repaired += int(context.get("repaired_count") or 0)
            manual_review += int(context.get("manual_review_count") or 0)
        status = _status_for_count(manual_review, warning=1, critical=10)
        alerts = []
        if manual_review:
            alerts.append(cls._alert(code="payout_repair_manual_review", severity=status, title="Payout repairs need manual review", detail="Some payout repair execution results still require manual review.", value=manual_review))
        return {
            "status": status,
            "window_hours": cls.DEFAULT_WINDOW_HOURS,
            "total_runs": total_runs,
            "repaired_count": repaired,
            "manual_review_count": manual_review,
            "repair_rate": _rate(numerator=repaired, denominator=max(repaired + manual_review, 0)),
        }, alerts

    @classmethod
    def _background_job_health(cls, *, since) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        outbox_total = OutboxMessage.objects.filter(created_at__gte=since).count()
        outbox_failed = OutboxMessage.objects.filter(status__in=[OutboxMessage.Status.FAILED, OutboxMessage.Status.DEAD]).count()
        inbox_failed = InboxMessage.objects.filter(status=InboxMessage.Status.FAILED, created_at__gte=since).count()
        backlog = OutboxMessage.objects.filter(status__in=[OutboxMessage.Status.PENDING, OutboxMessage.Status.PROCESSING]).count()
        status = _worst_status(
            _status_for_count(outbox_failed + inbox_failed, warning=1, critical=10),
            _status_for_count(backlog, warning=100, critical=1000),
        )
        alerts = []
        if outbox_failed or inbox_failed:
            alerts.append(cls._alert(code="background_job_failures", severity=status, title="Background job failures detected", detail="Outbox/inbox failed or dead messages exist.", value=outbox_failed + inbox_failed))
        if backlog >= 100:
            alerts.append(cls._alert(code="background_job_backlog", severity=status, title="Background job backlog detected", detail="Outbox pending/processing backlog is above threshold.", value=backlog))
        return {
            "status": status,
            "window_hours": cls.DEFAULT_WINDOW_HOURS,
            "outbox_total": outbox_total,
            "outbox_failed_or_dead": outbox_failed,
            "inbox_failed": inbox_failed,
            "outbox_backlog": backlog,
        }, alerts

    @classmethod
    def runtime_snapshot(cls, *, window_hours: int | None = None) -> dict[str, Any]:
        hours = max(1, min(int(window_hours or cls.DEFAULT_WINDOW_HOURS), 24 * 30))
        since = timezone.now() - timedelta(hours=hours)
        previous_default = cls.DEFAULT_WINDOW_HOURS
        cls.DEFAULT_WINDOW_HOURS = hours
        try:
            webhooks, webhook_alerts = cls._webhook_health(since=since)
            payments, payment_alerts = cls._payment_health(since=since)
            payout_repairs, payout_alerts = cls._payout_repair_health(since=since)
            background_jobs, job_alerts = cls._background_job_health(since=since)
        finally:
            cls.DEFAULT_WINDOW_HOURS = previous_default
        alerts = [*webhook_alerts, *payment_alerts, *payout_alerts, *job_alerts]
        health_indicators = [
            {"key": "webhooks", "status": webhooks["status"], "label": "Webhook failure rate"},
            {"key": "payments", "status": payments["status"], "label": "Payment error rate"},
            {"key": "payout_repairs", "status": payout_repairs["status"], "label": "Payout repair rate"},
            {"key": "background_jobs", "status": background_jobs["status"], "label": "Background job failures"},
        ]
        overall_status = _worst_status(*(item["status"] for item in health_indicators))
        return {
            "generated_at": timezone.now().isoformat(),
            "window_hours": hours,
            "overall_status": overall_status,
            "health_indicators": health_indicators,
            "webhooks": webhooks,
            "payments": payments,
            "payout_repairs": payout_repairs,
            "background_jobs": background_jobs,
            "alerts": alerts,
            "admin_ops_alerts": {
                "total": len(alerts),
                "critical": sum(1 for item in alerts if item["severity"] == "critical"),
                "degraded": sum(1 for item in alerts if item["severity"] == "degraded"),
                "items": alerts[:25],
            },
        }


def get_observability_runtime_snapshot(*, window_hours: int | None = None) -> dict[str, Any]:
    return ObservabilityRuntimeService.runtime_snapshot(window_hours=window_hours)
