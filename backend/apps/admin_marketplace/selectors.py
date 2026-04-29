from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Any, Callable

from django.db import connection
from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone


MoneyZero = Value(Decimal("0.00"), output_field=DecimalField(max_digits=14, decimal_places=2))


def _sum_money(field_name: str):
    return Coalesce(Sum(field_name), MoneyZero, output_field=DecimalField(max_digits=14, decimal_places=2))


def _safe_section(code: str, builder: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        payload = builder()
        payload.setdefault("status", "healthy")
        payload.setdefault("errors", [])
        return payload
    except Exception as exc:  # pragma: no cover - endpoint must degrade, not crash
        return {
            "status": "critical",
            "errors": [{"code": f"{code}_section_failed", "message": str(exc)}],
        }


def _decimal_to_str(value: Any) -> str:
    if value is None:
        return "0.00"
    if isinstance(value, Decimal):
        return str(value.quantize(Decimal("0.01")))
    return str(value)


def _count_by_status(model, *, status_field: str = "status") -> list[dict[str, Any]]:
    return list(
        model.objects.values(status_field)
        .annotate(count=Count("id"))
        .order_by(status_field)
        .values("count", status_field)
    )


def _audit_event_dict(event) -> dict[str, Any]:
    actor = getattr(event, "actor", None)
    return {
        "id": str(event.id),
        "actor_id": str(event.actor_id) if event.actor_id else None,
        "actor_email": getattr(actor, "email", "") if actor else "",
        "event_type": event.event_type,
        "entity_type": event.entity_type,
        "entity_id": event.entity_id,
        "context": event.context or {},
        "ip_address": event.ip_address,
        "created_at": event.created_at,
    }


class MarketplaceHealthSelector:
    """Aggregates operational marketplace health for the admin command center.

    The selector is intentionally defensive: one broken subdomain should mark the
    section as degraded but must not break the whole admin cockpit.
    """

    @classmethod
    def build(cls, *, days: int = 30) -> dict[str, Any]:
        days = max(1, min(int(days or 30), 365))
        generated_at = timezone.now()

        sections = {
            "system": _safe_section("system", cls._system_section),
            "moderation": _safe_section("moderation", cls._moderation_section),
            "trainer_onboarding": _safe_section("trainer_onboarding", cls._trainer_onboarding_section),
            "payouts": _safe_section("payouts", cls._payouts_section),
            "payments": _safe_section("payments", lambda: cls._payments_section(days=days)),
            "analytics": _safe_section("analytics", lambda: cls._analytics_section(days=days)),
            "reviews": _safe_section("reviews", cls._reviews_section),
            "audit": _safe_section("audit", cls._audit_section),
        }

        alerts = cls._build_alerts(sections)
        overall_status = cls._overall_status(alerts, sections)
        summary = cls._summary_from_sections(sections)

        return {
            "generated_at": generated_at,
            "range_days": days,
            "overall_status": overall_status,
            "summary": summary,
            "alerts": alerts,
            **sections,
        }

    @staticmethod
    def _overall_status(alerts: list[dict[str, Any]], sections: dict[str, dict[str, Any]]) -> str:
        if any(section.get("status") == "critical" for section in sections.values()):
            return "critical"
        if any(alert.get("severity") == "critical" for alert in alerts):
            return "critical"
        if alerts or any(section.get("status") == "warning" for section in sections.values()):
            return "warning"
        return "healthy"

    @staticmethod
    def _system_section() -> dict[str, Any]:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return {
            "status": "healthy",
            "database": "ok",
            "server_time": timezone.now(),
        }

    @staticmethod
    def _moderation_section() -> dict[str, Any]:
        from apps.moderation.models import ModerationCase, TrainerRiskFlag

        totals = ModerationCase.objects.aggregate(
            total=Count("id"),
            open=Count("id", filter=Q(status="open")),
            in_review=Count("id", filter=Q(status="in_review")),
            escalated=Count("id", filter=Q(status="escalated")),
            resolved=Count("id", filter=Q(status="resolved")),
        )
        queues = list(
            ModerationCase.objects.values("queue")
            .annotate(
                total=Count("id"),
                open=Count("id", filter=Q(status__in=["open", "in_review", "escalated"])),
            )
            .order_by("queue")
        )
        active_risk_flags = TrainerRiskFlag.objects.filter(is_active=True).count()
        critical_risk_flags = TrainerRiskFlag.objects.filter(is_active=True, risk_level="critical").count()
        latest_cases = [
            {
                "id": str(case.id),
                "queue": case.queue,
                "status": case.status,
                "target_type": case.target_type,
                "target_id": case.target_id,
                "title": case.title,
                "priority": case.priority,
                "latest_decision": case.latest_decision,
                "opened_at": case.opened_at,
            }
            for case in ModerationCase.objects.select_related("trainer", "assigned_to").order_by("priority", "-opened_at")[:8]
        ]
        status_value = "critical" if critical_risk_flags else "warning" if totals.get("escalated") else "healthy"
        return {
            "status": status_value,
            "totals": totals,
            "queues": queues,
            "active_risk_flags": active_risk_flags,
            "critical_risk_flags": critical_risk_flags,
            "latest_cases": latest_cases,
        }

    @staticmethod
    def _trainer_onboarding_section() -> dict[str, Any]:
        from apps.trainers.models import TrainerApplication, TrainerProfile
        from apps.users.models import User

        rows = _count_by_status(TrainerApplication)
        status_map = {row["status"]: row["count"] for row in rows}
        submitted_without_case = TrainerApplication.objects.filter(
            status__in=["submitted", "under_review"], latest_moderation_case_id__isnull=True
        ).count()
        approved_without_role = TrainerApplication.objects.filter(status="approved").exclude(user__role=User.Roles.TRAINER).count()
        approved_user_ids = TrainerApplication.objects.filter(status="approved").values_list("user_id", flat=True)
        approved_without_profile = TrainerApplication.objects.filter(status="approved").exclude(
            user_id__in=TrainerProfile.objects.filter(user_id__in=approved_user_ids).values_list("user_id", flat=True)
        ).count()

        status_value = "warning" if submitted_without_case or approved_without_role or approved_without_profile else "healthy"
        return {
            "status": status_value,
            "status_counts": rows,
            "submitted_without_case": submitted_without_case,
            "approved_without_role": approved_without_role,
            "approved_without_profile": approved_without_profile,
            "under_review_count": status_map.get("under_review", 0) + status_map.get("submitted", 0),
            "approved_count": status_map.get("approved", 0),
        }

    @staticmethod
    def _payouts_section() -> dict[str, Any]:
        from apps.payouts.selectors import get_admin_payout_operations_overview
        from apps.payouts.services import PayoutService

        overview = get_admin_payout_operations_overview()
        reconciliation = PayoutService.build_reconciliation_report()
        issue_count = int(reconciliation.get("issue_count") or len(reconciliation.get("issues") or []))
        status_value = "warning" if issue_count else "healthy"
        return {
            "status": status_value,
            "overview": overview,
            "reconciliation": reconciliation,
        }

    @staticmethod
    def _payments_section(*, days: int) -> dict[str, Any]:
        from apps.payments.models import Payment

        since = timezone.now() - timedelta(days=days)
        amount_field = "amount" if any(field.name == "amount" for field in Payment._meta.fields) else "gross_amount"
        status_rows = list(
            Payment.objects.values("status")
            .annotate(count=Count("id"), amount=_sum_money(amount_field))
            .order_by("status")
        )
        failed_statuses = ["failed", "cancelled"]
        paid_statuses = ["succeeded", "paid"]
        failed_recent = Payment.objects.filter(status__in=failed_statuses, created_at__gte=since).count() if hasattr(Payment, "created_at") else Payment.objects.filter(status__in=failed_statuses).count()
        paid_recent = Payment.objects.filter(status__in=paid_statuses, created_at__gte=since).count() if hasattr(Payment, "created_at") else Payment.objects.filter(status__in=paid_statuses).count()
        recent_failed = [
            {
                "id": str(payment.id),
                "status": payment.status,
                "amount": _decimal_to_str(getattr(payment, amount_field, Decimal("0.00"))),
                "currency": getattr(payment, "currency", "RUB"),
                "created_at": getattr(payment, "created_at", None),
            }
            for payment in Payment.objects.filter(status__in=failed_statuses).order_by("-created_at")[:8]
        ]
        return {
            "status": "warning" if failed_recent else "healthy",
            "statuses": status_rows,
            "failed_last_period": failed_recent,
            "paid_last_period": paid_recent,
            "recent_failed": recent_failed,
        }

    @staticmethod
    def _analytics_section(*, days: int) -> dict[str, Any]:
        from apps.analytics.selectors.kpi_selectors import KPISelectors

        overview = KPISelectors.overview(days=days)
        warehouse_health = KPISelectors.warehouse_health()
        warehouse_status = warehouse_health.get("status") or "empty"
        return {
            "status": "healthy" if warehouse_status == "healthy" else "warning",
            "overview": overview,
            "warehouse_health": warehouse_health,
        }

    @staticmethod
    def _reviews_section() -> dict[str, Any]:
        from apps.reviews.models import Review

        rows = _count_by_status(Review)
        pending_count = Review.objects.filter(status="pending").count()
        latest_pending = [
            {
                "id": str(review.id),
                "target_type": review.target_type,
                "target_id": review.target_id,
                "rating": review.rating,
                "title": review.title,
                "created_at": review.created_at,
            }
            for review in Review.objects.filter(status="pending").order_by("-created_at")[:8]
        ]
        return {
            "status": "warning" if pending_count else "healthy",
            "status_counts": rows,
            "pending_count": pending_count,
            "latest_pending": latest_pending,
        }

    @staticmethod
    def _audit_section() -> dict[str, Any]:
        from apps.audit.models import AuditEvent

        latest_events = [_audit_event_dict(event) for event in AuditEvent.objects.select_related("actor").order_by("-created_at")[:12]]
        action_counts = list(
            AuditEvent.objects.values("event_type")
            .annotate(count=Count("id"))
            .order_by("-count", "event_type")[:12]
        )
        return {
            "status": "healthy",
            "latest_events": latest_events,
            "action_counts": action_counts,
        }

    @staticmethod
    def _summary_from_sections(sections: dict[str, dict[str, Any]]) -> dict[str, Any]:
        analytics_overview = (sections.get("analytics") or {}).get("overview") or {}
        payout_overview = (sections.get("payouts") or {}).get("overview") or {}
        payout_ops = payout_overview.get("ops") or {}
        payout_reconciliation = (sections.get("payouts") or {}).get("reconciliation") or {}
        moderation_totals = (sections.get("moderation") or {}).get("totals") or {}
        onboarding = sections.get("trainer_onboarding") or {}
        reviews = sections.get("reviews") or {}
        payments = sections.get("payments") or {}
        return {
            "revenue": _decimal_to_str(analytics_overview.get("revenue")),
            "paid_orders": int(analytics_overview.get("paid_orders") or 0),
            "open_moderation_cases": int(moderation_totals.get("open") or 0)
            + int(moderation_totals.get("in_review") or 0)
            + int(moderation_totals.get("escalated") or 0),
            "active_risk_flags": int((sections.get("moderation") or {}).get("active_risk_flags") or 0),
            "under_review_applications": int(onboarding.get("under_review_count") or 0),
            "approved_trainers": int(onboarding.get("approved_count") or 0),
            "pending_payout_amount": _decimal_to_str(payout_ops.get("pending_exposure_amount")),
            "pending_payout_count": int(payout_ops.get("pending_exposure_count") or 0),
            "payout_reconciliation_issues": int(payout_reconciliation.get("issue_count") or len(payout_reconciliation.get("issues") or [])),
            "failed_payments": int(payments.get("failed_last_period") or 0),
            "pending_reviews": int(reviews.get("pending_count") or 0),
        }

    @staticmethod
    def _build_alerts(sections: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        for key, section in sections.items():
            for error in section.get("errors") or []:
                alerts.append({"severity": "critical", "code": error.get("code", f"{key}_error"), "message": error.get("message", "Section failed"), "section": key})

        moderation = sections.get("moderation") or {}
        if moderation.get("critical_risk_flags"):
            alerts.append({"severity": "critical", "code": "critical_trainer_risk_flags", "message": "Есть активные critical risk flags.", "section": "moderation"})
        if (moderation.get("totals") or {}).get("escalated"):
            alerts.append({"severity": "warning", "code": "escalated_moderation_cases", "message": "Есть escalated moderation cases.", "section": "moderation"})

        onboarding = sections.get("trainer_onboarding") or {}
        for metric in ["submitted_without_case", "approved_without_role", "approved_without_profile"]:
            if onboarding.get(metric):
                alerts.append({"severity": "warning", "code": metric, "message": f"Trainer onboarding integrity issue: {metric}.", "section": "trainer_onboarding"})

        payouts = sections.get("payouts") or {}
        reconciliation = payouts.get("reconciliation") or {}
        issue_count = int(reconciliation.get("issue_count") or len(reconciliation.get("issues") or []))
        if issue_count:
            alerts.append({"severity": "warning", "code": "payout_reconciliation_issues", "message": f"Payout reconciliation issues: {issue_count}.", "section": "payouts"})

        payments = sections.get("payments") or {}
        if payments.get("failed_last_period"):
            alerts.append({"severity": "warning", "code": "failed_payments", "message": "Есть failed/cancelled payments за выбранный период.", "section": "payments"})

        analytics = sections.get("analytics") or {}
        if (analytics.get("warehouse_health") or {}).get("status") != "healthy":
            alerts.append({"severity": "warning", "code": "analytics_warehouse_not_ready", "message": "Analytics warehouse еще пустой или не обновлялся.", "section": "analytics"})

        reviews = sections.get("reviews") or {}
        if reviews.get("pending_count"):
            alerts.append({"severity": "warning", "code": "pending_reviews", "message": "Есть отзывы на ручной модерации.", "section": "reviews"})
        return alerts
