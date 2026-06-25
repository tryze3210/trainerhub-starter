from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone


MONEY_ZERO = Value(Decimal("0.00"), output_field=DecimalField(max_digits=14, decimal_places=2))


def _money_sum(field_name: str):
    return Coalesce(Sum(field_name), MONEY_ZERO, output_field=DecimalField(max_digits=14, decimal_places=2))


def _money(value: Any) -> str:
    if value is None:
        return "0.00"
    if isinstance(value, Decimal):
        return str(value.quantize(Decimal("0.01")))
    try:
        return str(Decimal(str(value)).quantize(Decimal("0.01")))
    except Exception:
        return str(value)


def _iso(value: Any) -> str | None:
    return value.isoformat() if value else None


def _date(value: Any) -> str:
    return value.isoformat() if value else ""


def _safe_status_rows(queryset, field_name: str = "status") -> list[dict[str, Any]]:
    return [
        {"status": row[field_name] or "unknown", "count": row["count"]}
        for row in queryset.values(field_name).annotate(count=Count("id")).order_by(field_name)
    ]


class TrainerBusinessDashboardSelector:
    """Read-side aggregation for the trainer business cockpit.

    This selector intentionally avoids schema changes. It composes existing
    content, checkout/payment, payout and moderation tables into one payload for
    the trainer UI. If one optional domain has no data yet, the dashboard returns
    zeros instead of failing.
    """

    @classmethod
    def build(cls, *, user, trainer_id, days: int = 30) -> dict[str, Any]:
        days = max(1, min(int(days or 30), 365))
        today = timezone.localdate()
        start_date = today - timedelta(days=days - 1)

        return {
            "generated_at": timezone.now().isoformat(),
            "range_days": days,
            "trainer_id": str(trainer_id),
            "application": cls._application_section(user),
            "profile": cls._profile_section(user=user, trainer_id=trainer_id),
            "content": cls._content_section(trainer_id=trainer_id),
            "commerce": cls._commerce_section(user=user, trainer_id=trainer_id, start_date=start_date),
            "payouts": cls._payout_section(user=user),
            "moderation": cls._moderation_section(user=user),
            "readiness": cls._readiness_section(user=user, trainer_id=trainer_id),
        }

    @staticmethod
    def _application_section(user) -> dict[str, Any] | None:
        from apps.trainers.models import TrainerApplication

        application = TrainerApplication.objects.filter(user=user).first()
        if not application:
            return None
        return {
            "id": str(application.id),
            "status": application.status,
            "brand_name": application.brand_name,
            "legal_name": application.legal_name,
            "submitted_at": _iso(application.submitted_at),
            "reviewed_at": _iso(application.reviewed_at),
            "reviewer_note": application.reviewer_note,
            "latest_moderation_case_id": str(application.latest_moderation_case_id) if application.latest_moderation_case_id else None,
        }

    @staticmethod
    def _profile_section(*, user, trainer_id) -> dict[str, Any]:
        from apps.trainer_profiles.models import TrainerPublicProfile
        from apps.trainers.models import TrainerProfile

        legacy_profile = TrainerProfile.objects.filter(user=user).first()
        public_profile = TrainerPublicProfile.objects.filter(trainer_uuid=trainer_id).first()
        return {
            "legacy_profile": {
                "id": str(legacy_profile.id),
                "slug": legacy_profile.slug,
                "display_name": legacy_profile.display_name,
                "status": legacy_profile.status,
                "is_public": legacy_profile.is_public,
                "rating_avg": str(legacy_profile.rating_avg),
                "views_count": legacy_profile.views_count,
                "sales_count": legacy_profile.sales_count,
            }
            if legacy_profile
            else None,
            "public_profile": {
                "id": str(public_profile.id),
                "slug": public_profile.slug,
                "display_name": public_profile.display_name,
                "is_public": public_profile.is_public,
            }
            if public_profile
            else None,
        }

    @staticmethod
    def _content_section(*, trainer_id) -> dict[str, Any]:
        from apps.content.models import PublishedBundle, PublishedProgram, PublishedVideo
        from apps.trainer_cms.models import (
            PublishStatus,
            TrainerBundleDraft,
            TrainerCourseDraft,
            TrainerProgramDraft,
            TrainerVideoDraft,
        )

        draft_video_qs = TrainerVideoDraft.objects.filter(trainer_id=trainer_id)
        draft_course_qs = TrainerCourseDraft.objects.filter(trainer_id=trainer_id)
        draft_program_qs = TrainerProgramDraft.objects.filter(trainer_id=trainer_id)
        draft_bundle_qs = TrainerBundleDraft.objects.filter(trainer_id=trainer_id)

        published_video_qs = PublishedVideo.objects.filter(trainer_profile__trainer_uuid=trainer_id)
        published_program_qs = PublishedProgram.objects.filter(trainer_profile__trainer_uuid=trainer_id)
        published_bundle_qs = PublishedBundle.objects.filter(trainer_profile__trainer_uuid=trainer_id)

        draft_status_counts = {
            "videos": _safe_status_rows(draft_video_qs),
            "courses": _safe_status_rows(draft_course_qs),
            "programs": _safe_status_rows(draft_program_qs),
            "bundles": _safe_status_rows(draft_bundle_qs),
        }
        pending_review_count = (
            draft_video_qs.filter(status=PublishStatus.REVIEW).count()
            + draft_course_qs.filter(status=PublishStatus.REVIEW).count()
            + draft_program_qs.filter(status=PublishStatus.REVIEW).count()
            + draft_bundle_qs.filter(status=PublishStatus.REVIEW).count()
        )

        latest_items: list[dict[str, Any]] = []
        for entity_type, queryset in [
            ("video", published_video_qs),
            ("program", published_program_qs),
            ("bundle", published_bundle_qs),
        ]:
            for item in queryset.order_by("-published_at", "-created_at")[:5]:
                latest_items.append(
                    {
                        "entity_type": entity_type,
                        "id": str(item.id),
                        "slug": item.slug,
                        "title": item.title,
                        "price_amount": _money(item.price_amount),
                        "currency": item.currency,
                        "is_active": item.is_active,
                        "published_at": _iso(item.published_at),
                    }
                )
        latest_items.sort(key=lambda row: row.get("published_at") or "", reverse=True)

        return {
            "drafts": {
                "videos": draft_video_qs.count(),
                "courses": draft_course_qs.count(),
                "programs": draft_program_qs.count(),
                "bundles": draft_bundle_qs.count(),
                "total": draft_video_qs.count() + draft_course_qs.count() + draft_program_qs.count() + draft_bundle_qs.count(),
            },
            "published": {
                "videos": published_video_qs.filter(is_active=True).count(),
                "programs": published_program_qs.filter(is_active=True).count(),
                "bundles": published_bundle_qs.filter(is_active=True).count(),
                "total": published_video_qs.filter(is_active=True).count()
                + published_program_qs.filter(is_active=True).count()
                + published_bundle_qs.filter(is_active=True).count(),
            },
            "draft_status_counts": draft_status_counts,
            "pending_review_count": pending_review_count,
            "latest_published": latest_items[:8],
        }

    @staticmethod
    def _commerce_section(*, user, trainer_id, start_date) -> dict[str, Any]:
        from apps.orders.models import Order, OrderItem
        from apps.payments.models import Payment, PaymentStatus

        trainer_ids = [str(user.id), str(trainer_id)]
        trainer_filter = Q(provider_payload__trainer_id=trainer_ids[0]) | Q(provider_payload__trainer_id=trainer_ids[1])
        item_filter = Q(metadata__trainer_id=trainer_ids[0]) | Q(metadata__trainer_id=trainer_ids[1]) | Q(order__payments__provider_payload__trainer_id=trainer_ids[0]) | Q(order__payments__provider_payload__trainer_id=trainer_ids[1])
        paid_payment_statuses = [PaymentStatus.SUCCEEDED, "paid"]
        paid_order_statuses = ["paid", "completed"]

        paid_payments = Payment.objects.filter(
            trainer_filter,
            status__in=paid_payment_statuses,
        )
        paid_payments_period = paid_payments.filter(confirmed_at__date__gte=start_date)

        order_items = OrderItem.objects.filter(
            item_filter,
            order__status__in=paid_order_statuses,
        ).distinct()
        order_items_period = order_items.filter(Q(order__paid_at__date__gte=start_date) | Q(order__completed_at__date__gte=start_date))

        revenue_total = paid_payments.aggregate(total=_money_sum("amount"))["total"] or Decimal("0.00")
        revenue_period = paid_payments_period.aggregate(total=_money_sum("amount"))["total"] or Decimal("0.00")
        paid_orders_count = paid_payments.values("order_id").distinct().count()
        period_orders_count = paid_payments_period.values("order_id").distinct().count()
        customers_count = paid_payments.values("order__user_id").distinct().count()

        avg_order_value = Decimal("0.00")
        if paid_orders_count:
            avg_order_value = (revenue_total / Decimal(paid_orders_count)).quantize(Decimal("0.01"))

        payment_rows = (
            paid_payments_period.annotate(day=TruncDate("confirmed_at"))
            .values("day")
            .annotate(revenue=_money_sum("amount"), orders_count=Count("order_id", distinct=True))
            .order_by("day")
        )
        payment_map = {row["day"]: row for row in payment_rows if row["day"]}
        today = timezone.localdate()
        days = (today - start_date).days + 1
        revenue_series = []
        for offset in range(days):
            day = start_date + timedelta(days=offset)
            row = payment_map.get(day, {})
            revenue_series.append(
                {
                    "date": _date(day),
                    "revenue": _money(row.get("revenue", Decimal("0.00"))),
                    "orders_count": int(row.get("orders_count") or 0),
                }
            )

        top_products = [
            {
                "item_type": row["item_type"],
                "title": row["title_snapshot"] or "Untitled",
                "revenue": _money(row["revenue"]),
                "orders_count": row["orders_count"],
            }
            for row in order_items.values("item_type", "title_snapshot")
            .annotate(revenue=_money_sum("total_price"), orders_count=Count("order_id", distinct=True))
            .order_by("-revenue", "-orders_count")[:10]
        ]

        latest_orders = [
            {
                "id": str(order.id),
                "status": order.status,
                "total_amount": _money(order.total_amount),
                "currency": order.currency,
                "paid_at": _iso(order.paid_at),
                "completed_at": _iso(order.completed_at),
            }
            for order in Order.objects.filter(payments__in=paid_payments).distinct().order_by("-paid_at", "-created_at")[:8]
        ]

        return {
            "revenue_total": _money(revenue_total),
            "revenue_period": _money(revenue_period),
            "paid_orders_count": paid_orders_count,
            "period_orders_count": period_orders_count,
            "customers_count": customers_count,
            "avg_order_value": _money(avg_order_value),
            "order_items_count": order_items.count(),
            "order_items_period_count": order_items_period.count(),
            "revenue_series": revenue_series,
            "top_products": top_products,
            "latest_orders": latest_orders,
        }

    @staticmethod
    def _payout_section(*, user) -> dict[str, Any]:
        from apps.payouts.selectors import list_payout_requests_for_trainer
        from apps.payouts.services import PayoutService

        balance = PayoutService.get_or_create_balance(trainer_id=user.id)
        requests_qs = list_payout_requests_for_trainer(user.id)
        active_statuses = ["requested", "pending", "approved", "processing"]
        status_counts = _safe_status_rows(requests_qs)
        latest_requests = [
            {
                "id": str(item.id),
                "amount": _money(item.amount),
                "currency": item.currency,
                "status": item.status,
                "destination_masked": item.destination_masked,
                "requested_at": _iso(item.requested_at),
                "approved_at": item.approved_at,
                "processed_at": item.processed_at,
                "rejected_reason": item.rejected_reason,
            }
            for item in requests_qs[:8]
        ]
        return {
            "balance": {
                "trainer_id": str(user.id),
                "currency": balance.currency,
                "available_amount": _money(balance.available_amount),
                "reserved_amount": _money(balance.reserved_amount),
                "lifetime_earned_amount": _money(balance.lifetime_earned_amount),
                "updated_at": _iso(balance.updated_at),
            },
            "status_counts": status_counts,
            "requests_count": requests_qs.count(),
            "active_requests_count": requests_qs.filter(status__in=active_statuses).count(),
            "latest_requests": latest_requests,
            "can_request_payout": balance.available_amount > Decimal("0.00"),
        }

    @staticmethod
    def _moderation_section(*, user) -> dict[str, Any]:
        from apps.moderation.models import ModerationCase, TrainerRiskFlag

        cases = ModerationCase.objects.filter(Q(trainer=user) | Q(target_id=str(user.id))).distinct()
        risk_flags = TrainerRiskFlag.objects.filter(trainer=user, is_active=True)
        latest_cases = [
            {
                "id": str(case.id),
                "queue": case.queue,
                "status": case.status,
                "target_type": case.target_type,
                "title": case.title,
                "latest_decision": case.latest_decision,
                "opened_at": _iso(case.opened_at),
            }
            for case in cases.order_by("priority", "-opened_at")[:8]
        ]
        return {
            "open_cases_count": cases.filter(status__in=["open", "in_review", "escalated"]).count(),
            "risk_flags_count": risk_flags.count(),
            "critical_risk_flags_count": risk_flags.filter(risk_level="critical").count(),
            "latest_cases": latest_cases,
        }

    @classmethod
    def _readiness_section(cls, *, user, trainer_id) -> dict[str, Any]:
        application = cls._application_section(user)
        content = cls._content_section(trainer_id=trainer_id)
        profile = cls._profile_section(user=user, trainer_id=trainer_id)
        payouts = cls._payout_section(user=user)
        moderation = cls._moderation_section(user=user)

        checks = [
            {
                "code": "application_approved",
                "title": "Заявка тренера одобрена",
                "status": "done" if application and application["status"] == "approved" else "blocker",
            },
            {
                "code": "public_profile_ready",
                "title": "Публичный профиль создан",
                "status": "done" if profile.get("public_profile") else "warning",
            },
            {
                "code": "has_published_content",
                "title": "Есть опубликованный продукт",
                "status": "done" if (content.get("published") or {}).get("total", 0) > 0 else "warning",
            },
            {
                "code": "no_blocking_moderation",
                "title": "Нет критичных moderation flags",
                "status": "done" if moderation.get("critical_risk_flags_count", 0) == 0 else "blocker",
            },
            {
                "code": "payout_ready",
                "title": "Есть доступный баланс для выплаты",
                "status": "done" if payouts.get("can_request_payout") else "warning",
            },
        ]
        blockers = [item for item in checks if item["status"] == "blocker"]
        warnings = [item for item in checks if item["status"] == "warning"]
        return {
            "status": "blocked" if blockers else "attention" if warnings else "ready",
            "checks": checks,
            "blockers_count": len(blockers),
            "warnings_count": len(warnings),
        }
