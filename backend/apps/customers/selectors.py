from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from uuid import UUID
from typing import Any

from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.customers.models import CustomerNote, CustomerProfile, CustomerSegment
from apps.entitlements.models import Entitlement, EntitlementStatus
from apps.favorites.models import Favorite
from apps.orders.models import Order, OrderStatus
from apps.payments.models import Payment, PaymentStatus
from apps.reviews.models import Review
from apps.subscriptions.models import Subscription, SubscriptionStatus


def _money(value: Any) -> str:
    if value is None:
        value = Decimal("0.00")
    if not isinstance(value, Decimal):
        try:
            value = Decimal(str(value))
        except Exception:
            value = Decimal("0.00")
    return f"{value.quantize(Decimal('0.01'))}"


def _iso(value: Any) -> str | None:
    return value.isoformat() if value else None


def _uuid(value: Any) -> str | None:
    return str(value) if value else None


def _is_uuid(value: Any) -> bool:
    try:
        UUID(str(value))
        return True
    except Exception:
        return False


def _is_intish(value: Any) -> bool:
    return str(value).isdigit()


class CustomerMarketplaceHubSelector:
    """Read-side aggregation for the buyer-facing marketplace cabinet.

    This selector intentionally does not create new tables. It composes existing
    orders, payments, entitlements, subscriptions, favorites, reviews and public
    content into one stable API payload for the customer dashboard.
    """

    def build(self, *, user, days: int = 30) -> dict[str, Any]:
        days = max(1, min(int(days or 30), 365))
        start_date = timezone.localdate() - timedelta(days=days - 1)
        profile = self._profile_section(user=user)
        entitlements = self._entitlements_section(user=user)
        orders = self._orders_section(user=user, start_date=start_date)
        payments = self._payments_section(user=user, start_date=start_date)
        subscriptions = self._subscriptions_section(user=user)
        favorites = self._favorites_section(user=user)
        reviews = self._reviews_section(user=user, entitlements=entitlements["items"])
        recommendations = self._recommendations_section(user=user, entitlements=entitlements["items"], favorites=favorites["items"])

        return {
            "profile": profile,
            "summary": {
                "period_days": days,
                "active_entitlements_count": entitlements["summary"]["active_count"],
                "active_subscriptions_count": subscriptions["summary"]["active_count"],
                "paid_orders_count": orders["summary"]["paid_orders_count"],
                "orders_period_count": orders["summary"]["orders_period_count"],
                "total_spent": orders["summary"]["total_spent"],
                "period_spent": orders["summary"]["period_spent"],
                "favorites_count": favorites["summary"]["total_count"],
                "review_opportunities_count": reviews["summary"]["review_opportunities_count"],
                "failed_payments_count": payments["summary"]["failed_count"],
            },
            "library": entitlements,
            "orders": orders,
            "payments": payments,
            "subscriptions": subscriptions,
            "favorites": favorites,
            "reviews": reviews,
            "recommendations": recommendations,
            "readiness": self._readiness_section(entitlements=entitlements, orders=orders, payments=payments, subscriptions=subscriptions),
        }

    @staticmethod
    def _profile_section(*, user) -> dict[str, Any]:
        profile, _ = CustomerProfile.objects.get_or_create(
            user=user,
            defaults={"display_name": getattr(user, "display_name", "") or getattr(user, "full_name", "") or getattr(user, "email", "")},
        )
        return {
            "id": str(profile.id),
            "display_name": profile.display_name or getattr(user, "display_name", "") or getattr(user, "full_name", "") or getattr(user, "email", ""),
            "email": getattr(user, "email", ""),
            "bio": profile.bio,
            "streak_count": profile.streak_count,
            "active_role": getattr(user, "role", "customer"),
            "created_at": _iso(profile.created_at),
        }

    def _entitlements_section(self, *, user) -> dict[str, Any]:
        queryset = (
            Entitlement.objects.filter(user=user)
            .select_related("source_order", "source_subscription")
            .order_by("-created_at")
        )
        active_statuses = [EntitlementStatus.ACTIVE, "active"]
        items = [self._entitlement_item(entitlement) for entitlement in queryset[:80]]
        active_count = queryset.filter(status__in=active_statuses).count()
        by_type: dict[str, int] = {}
        for item in items:
            by_type[item["target_type"]] = by_type.get(item["target_type"], 0) + 1
        return {
            "summary": {
                "total_count": queryset.count(),
                "active_count": active_count,
                "by_type": by_type,
            },
            "items": items,
        }

    def _entitlement_item(self, entitlement: Entitlement) -> dict[str, Any]:
        content = self._resolve_content(entitlement.target_type, entitlement.target_id)
        return {
            "id": str(entitlement.id),
            "source_type": entitlement.source_type,
            "source_order_id": _uuid(entitlement.source_order_id),
            "source_subscription_id": _uuid(entitlement.source_subscription_id),
            "target_type": entitlement.target_type,
            "target_id": _uuid(entitlement.target_id),
            "status": entitlement.status,
            "starts_at": _iso(entitlement.starts_at),
            "ends_at": _iso(entitlement.ends_at),
            "created_at": _iso(entitlement.created_at),
            "metadata": entitlement.metadata or {},
            "content": content,
            "title": content.get("title") or (entitlement.metadata or {}).get("title") or entitlement.target_type,
            "trainer_name": content.get("trainer_name") or (entitlement.metadata or {}).get("trainer_name") or "",
            "slug": content.get("slug") or "",
            "access_status": "available" if entitlement.status == EntitlementStatus.ACTIVE else entitlement.status,
        }

    @staticmethod
    def _resolve_content(target_type: str, target_id: Any) -> dict[str, Any]:
        if not target_id:
            return {}
        try:
            from apps.content.models import PublishedBundle, PublishedProgram, PublishedVideo
        except Exception:
            return {}

        model_map = {
            "video": PublishedVideo,
            "program": PublishedProgram,
            "bundle": PublishedBundle,
        }
        model = model_map.get(str(target_type))
        if not model:
            return {}
        lookup = Q(source_draft_id=target_id) if _is_uuid(target_id) else Q(slug=str(target_id))
        if _is_intish(target_id):
            lookup = lookup | Q(id=int(str(target_id)))
        obj = model.objects.select_related("trainer_profile").filter(lookup).first()
        if not obj:
            return {}
        return {
            "id": str(obj.id),
            "slug": obj.slug,
            "title": obj.title,
            "description": obj.description,
            "target_type": target_type,
            "trainer_slug": getattr(obj.trainer_profile, "slug", ""),
            "trainer_name": getattr(obj.trainer_profile, "display_name", ""),
            "category": getattr(obj, "category", ""),
            "difficulty": getattr(obj, "difficulty", ""),
            "duration_minutes": getattr(obj, "duration_minutes", 0),
            "price_amount": _money(getattr(obj, "price_amount", Decimal("0.00"))),
            "currency": getattr(obj, "currency", "RUB"),
        }

    def _orders_section(self, *, user, start_date) -> dict[str, Any]:
        paid_statuses = [OrderStatus.PAID, OrderStatus.COMPLETED, "paid", "completed"]
        queryset = Order.objects.filter(user=user).prefetch_related("items").order_by("-created_at")
        paid = queryset.filter(status__in=paid_statuses)
        period = queryset.filter(created_at__date__gte=start_date)
        period_paid = paid.filter(Q(paid_at__date__gte=start_date) | Q(completed_at__date__gte=start_date) | Q(created_at__date__gte=start_date))
        total_spent = paid.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
        period_spent = period_paid.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
        recent = [self._order_item(order) for order in queryset[:12]]
        return {
            "summary": {
                "total_orders_count": queryset.count(),
                "paid_orders_count": paid.count(),
                "orders_period_count": period.count(),
                "total_spent": _money(total_spent),
                "period_spent": _money(period_spent),
            },
            "recent": recent,
        }

    @staticmethod
    def _order_item(order: Order) -> dict[str, Any]:
        items = list(order.items.all()[:8])
        return {
            "id": str(order.id),
            "order_type": order.order_type,
            "status": order.status,
            "currency": order.currency,
            "total_amount": _money(order.total_amount),
            "created_at": _iso(order.created_at),
            "paid_at": _iso(order.paid_at),
            "completed_at": _iso(order.completed_at),
            "items_count": len(items),
            "items": [
                {
                    "id": str(item.id),
                    "item_type": item.item_type,
                    "item_id": str(item.item_id),
                    "title": item.title_snapshot,
                    "quantity": item.quantity,
                    "unit_price": _money(item.unit_price),
                    "total_price": _money(item.total_price),
                    "metadata": item.metadata or {},
                }
                for item in items
            ],
        }

    @staticmethod
    def _payments_section(*, user, start_date) -> dict[str, Any]:
        queryset = Payment.objects.filter(order__user=user).select_related("order").order_by("-created_at")
        failed_statuses = [PaymentStatus.FAILED, PaymentStatus.CANCELLED, "failed", "cancelled"]
        recent_failed = queryset.filter(status__in=failed_statuses)[:8]
        return {
            "summary": {
                "total_count": queryset.count(),
                "failed_count": queryset.filter(status__in=failed_statuses, created_at__date__gte=start_date).count(),
                "pending_count": queryset.filter(status__in=[PaymentStatus.CREATED, PaymentStatus.PENDING, "created", "pending"]).count(),
            },
            "recent_failed": [
                {
                    "id": str(payment.id),
                    "order_id": str(payment.order_id),
                    "provider": payment.provider,
                    "status": payment.status,
                    "amount": _money(payment.amount),
                    "currency": payment.currency,
                    "created_at": _iso(payment.created_at),
                }
                for payment in recent_failed
            ],
        }

    @staticmethod
    def _subscriptions_section(*, user) -> dict[str, Any]:
        active_statuses = [SubscriptionStatus.ACTIVE, "active"]
        queryset = Subscription.objects.filter(user=user).select_related("plan").order_by("-created_at")
        return {
            "summary": {
                "total_count": queryset.count(),
                "active_count": queryset.filter(status__in=active_statuses).count(),
            },
            "items": [
                {
                    "id": str(subscription.id),
                    "status": subscription.status,
                    "starts_at": _iso(subscription.starts_at),
                    "ends_at": _iso(subscription.ends_at),
                    "cancelled_at": _iso(subscription.cancelled_at),
                    "auto_renew": subscription.auto_renew,
                    "plan": {
                        "id": str(subscription.plan_id),
                        "code": subscription.plan.code,
                        "title": subscription.plan.title,
                        "period_days": subscription.plan.period_days,
                        "price": _money(subscription.plan.price),
                        "currency": subscription.plan.currency,
                    },
                }
                for subscription in queryset[:12]
            ],
        }

    def _favorites_section(self, *, user) -> dict[str, Any]:
        queryset = Favorite.objects.filter(user=user).order_by("-created_at")
        items = [self._favorite_item(favorite) for favorite in queryset[:30]]
        by_type: dict[str, int] = {}
        for item in items:
            by_type[item["target_type"]] = by_type.get(item["target_type"], 0) + 1
        return {
            "summary": {"total_count": queryset.count(), "by_type": by_type},
            "items": items,
        }

    def _favorite_item(self, favorite: Favorite) -> dict[str, Any]:
        target_type = favorite.target_type
        target_id = favorite.target_id
        target = self._resolve_favorite_target(target_type, target_id)
        return {
            "id": str(favorite.id),
            "target_type": target_type,
            "target_id": target_id,
            "created_at": _iso(favorite.created_at),
            "target": target,
            "title": target.get("title") or target.get("display_name") or target_id,
            "slug": target.get("slug") or "",
        }

    @staticmethod
    def _resolve_favorite_target(target_type: str, target_id: str) -> dict[str, Any]:
        if target_type == Favorite.TargetType.TRAINER:
            from apps.trainer_profiles.models import TrainerPublicProfile

            lookup = Q(slug=target_id)
            if _is_uuid(target_id):
                lookup = lookup | Q(trainer_uuid=target_id)
            if _is_intish(target_id):
                lookup = lookup | Q(id=int(target_id))
            trainer = TrainerPublicProfile.objects.filter(lookup).first()
            if not trainer:
                return {}
            return {
                "id": str(trainer.id),
                "slug": trainer.slug,
                "display_name": trainer.display_name,
                "title": trainer.display_name,
                "headline": trainer.headline,
                "rating_avg": str(trainer.rating_avg),
                "reviews_count": trainer.reviews_count,
            }
        if target_type in {Favorite.TargetType.VIDEO, Favorite.TargetType.PROGRAM}:
            model_name = "video" if target_type == Favorite.TargetType.VIDEO else "program"
            from apps.content.models import PublishedProgram, PublishedVideo

            model = PublishedVideo if model_name == "video" else PublishedProgram
            lookup = Q(slug=target_id)
            if _is_uuid(target_id):
                lookup = lookup | Q(source_draft_id=target_id)
            if _is_intish(target_id):
                lookup = lookup | Q(id=int(target_id))
            item = model.objects.select_related("trainer_profile").filter(lookup).first()
            if not item:
                return {}
            return {
                "id": str(item.id),
                "slug": item.slug,
                "title": item.title,
                "trainer_name": item.trainer_profile.display_name,
                "trainer_slug": item.trainer_profile.slug,
                "price_amount": _money(item.price_amount),
                "currency": item.currency,
            }
        return {}

    @staticmethod
    def _reviews_section(*, user, entitlements: list[dict[str, Any]]) -> dict[str, Any]:
        authored_reviews = Review.objects.filter(author_user_id=str(user.id)).order_by("-created_at")
        reviewed_keys = set(authored_reviews.values_list("target_type", "target_id"))
        opportunities = []
        for item in entitlements:
            target_type = item.get("target_type")
            target_id = item.get("target_id")
            if not target_type or not target_id:
                continue
            if (target_type, target_id) in reviewed_keys:
                continue
            opportunities.append(
                {
                    "target_type": target_type,
                    "target_id": target_id,
                    "title": item.get("title") or target_type,
                    "trainer_name": item.get("trainer_name") or "",
                    "slug": item.get("slug") or "",
                }
            )
            if len(opportunities) >= 8:
                break
        return {
            "summary": {
                "reviews_count": authored_reviews.count(),
                "review_opportunities_count": len(opportunities),
            },
            "opportunities": opportunities,
            "recent": [
                {
                    "id": str(review.id),
                    "target_type": review.target_type,
                    "target_id": review.target_id,
                    "rating": review.rating,
                    "title": review.title,
                    "status": review.status,
                    "created_at": _iso(review.created_at),
                }
                for review in authored_reviews[:8]
            ],
        }

    @staticmethod
    def _recommendations_section(*, user, entitlements: list[dict[str, Any]], favorites: list[dict[str, Any]]) -> dict[str, Any]:
        from apps.content.models import PublishedBundle, PublishedProgram, PublishedVideo

        entitled_ids = {item.get("target_id") for item in entitlements if item.get("target_id")}
        favorite_ids = {item.get("target_id") for item in favorites if item.get("target_id")}
        exclude_ids = entitled_ids | favorite_ids
        recommendations: list[dict[str, Any]] = []
        sources = [
            ("video", PublishedVideo.objects.select_related("trainer_profile").filter(is_active=True, visibility="public")),
            ("program", PublishedProgram.objects.select_related("trainer_profile").filter(is_active=True, visibility="public")),
            ("bundle", PublishedBundle.objects.select_related("trainer_profile").filter(is_active=True, visibility="public")),
        ]
        for target_type, queryset in sources:
            for item in queryset.order_by("-is_featured", "-published_at")[:12]:
                if str(item.id) in exclude_ids:
                    continue
                recommendations.append(
                    {
                        "target_type": target_type,
                        "target_id": str(item.id),
                        "slug": item.slug,
                        "title": item.title,
                        "trainer_name": item.trainer_profile.display_name,
                        "trainer_slug": item.trainer_profile.slug,
                        "category": item.category,
                        "difficulty": item.difficulty,
                        "price_amount": _money(item.price_amount),
                        "currency": item.currency,
                        "duration_minutes": item.duration_minutes,
                        "is_featured": item.is_featured,
                    }
                )
                if len(recommendations) >= 10:
                    return {"items": recommendations}
        return {"items": recommendations}

    @staticmethod
    def _readiness_section(*, entitlements: dict[str, Any], orders: dict[str, Any], payments: dict[str, Any], subscriptions: dict[str, Any]) -> dict[str, Any]:
        checks = [
            {
                "code": "has_library",
                "title": "Есть доступный контент",
                "status": "done" if entitlements["summary"]["active_count"] > 0 else "todo",
            },
            {
                "code": "has_paid_order",
                "title": "Есть оплаченные заказы",
                "status": "done" if orders["summary"]["paid_orders_count"] > 0 else "todo",
            },
            {
                "code": "has_subscription",
                "title": "Есть активная подписка",
                "status": "done" if subscriptions["summary"]["active_count"] > 0 else "optional",
            },
            {
                "code": "no_failed_payments",
                "title": "Нет проблемных платежей за период",
                "status": "done" if payments["summary"]["failed_count"] == 0 else "attention",
            },
        ]
        blocking = [item for item in checks if item["status"] in {"todo", "attention"}]
        return {
            "status": "ready" if not blocking else "attention",
            "checks": checks,
        }


class TrainerCRMSelector:
    def build(self, *, trainer, days: int = 90, search: str = "", limit: int = 100) -> dict[str, Any]:
        days = max(1, min(int(days or 90), 365))
        limit = max(1, min(int(limit or 100), 250))
        customer_ids = self._customer_ids_for_trainer(trainer=trainer, search=search)
        customers = list(
            trainer.__class__.objects
            .filter(id__in=customer_ids)
            .order_by("email")[:limit]
        )
        items = [self._customer_summary(trainer=trainer, customer=customer, days=days) for customer in customers]
        segments = self._segments(trainer=trainer)
        return {
            "summary": {
                "customers_count": len(items),
                "with_active_access_count": sum(1 for item in items if item["active_entitlements_count"] > 0),
                "with_notes_count": sum(1 for item in items if item["notes_count"] > 0),
                "segments_count": len(segments),
                "period_days": days,
            },
            "segments": segments,
            "items": items,
        }

    def detail(self, *, trainer, customer_id) -> dict[str, Any]:
        User = trainer.__class__
        customer = User.objects.get(id=customer_id)
        if str(customer.id) not in self._customer_ids_for_trainer(trainer=trainer):
            raise PermissionError("Customer is not connected to this trainer.")
        return {
            "customer": self._customer_summary(trainer=trainer, customer=customer, days=365),
            "purchase_history": self._purchase_history(trainer=trainer, customer=customer),
            "access_history": self._access_history(customer=customer),
            "attendance_history": self._attendance_history(trainer=trainer, customer=customer),
            "notes": self._notes(trainer=trainer, customer=customer),
            "segments": self._segments(trainer=trainer, customer=customer),
        }

    def _customer_ids_for_trainer(self, *, trainer, search: str = "") -> set[str]:
        trainer_ids = {str(trainer.id)}
        order_customer_ids = set(
            Order.objects.filter(
                Q(items__metadata__trainer_id__in=list(trainer_ids))
                | Q(payments__provider_payload__trainer_id__in=list(trainer_ids))
            )
            .values_list("user_id", flat=True)
            .distinct()
        )
        try:
            from apps.booking.models import SessionReservation

            booking_customer_ids = set(
                SessionReservation.objects.filter(trainer=trainer)
                .values_list("customer_id", flat=True)
                .distinct()
            )
        except Exception:
            booking_customer_ids = set()
        ids = {str(value) for value in order_customer_ids | booking_customer_ids if value}
        if search:
            search = search.strip()
            if search:
                User = trainer.__class__
                ids = set(
                    str(value)
                    for value in User.objects.filter(id__in=ids).filter(
                        Q(email__icontains=search)
                        | Q(first_name__icontains=search)
                        | Q(last_name__icontains=search)
                    ).values_list("id", flat=True)
                )
        return ids

    def _customer_summary(self, *, trainer, customer, days: int) -> dict[str, Any]:
        start_date = timezone.localdate() - timedelta(days=days - 1)
        profile, _ = CustomerProfile.objects.get_or_create(
            user=customer,
            defaults={"display_name": customer.email},
        )
        orders = self._trainer_orders(trainer=trainer, customer=customer)
        paid_orders = orders.filter(status__in=[OrderStatus.PAID, OrderStatus.COMPLETED])
        period_orders = paid_orders.filter(created_at__date__gte=start_date)
        total_spent = paid_orders.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
        period_spent = period_orders.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
        entitlements = Entitlement.objects.filter(user=customer)
        active_entitlements = entitlements.filter(status=EntitlementStatus.ACTIVE).count()
        notes_count = CustomerNote.objects.filter(trainer=trainer, customer=customer).count()
        segment_rows = self._segments(trainer=trainer, customer=customer)
        last_order = paid_orders.order_by("-created_at").first()
        return {
            "customer_id": str(customer.id),
            "profile_id": str(profile.id),
            "email": customer.email,
            "display_name": profile.display_name or customer.get_full_name() or customer.email,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "created_at": _iso(customer.created_at),
            "orders_count": orders.count(),
            "paid_orders_count": paid_orders.count(),
            "total_spent": _money(total_spent),
            "period_spent": _money(period_spent),
            "active_entitlements_count": active_entitlements,
            "notes_count": notes_count,
            "segments": segment_rows,
            "last_order_at": _iso(last_order.created_at if last_order else None),
            "status": "active" if active_entitlements else "lead",
        }

    @staticmethod
    def _trainer_orders(*, trainer, customer):
        return (
            Order.objects.filter(user=customer)
            .filter(
                Q(items__metadata__trainer_id=str(trainer.id))
                | Q(payments__provider_payload__trainer_id=str(trainer.id))
            )
            .distinct()
            .prefetch_related("items")
            .order_by("-created_at")
        )

    def _purchase_history(self, *, trainer, customer) -> list[dict[str, Any]]:
        return [CustomerMarketplaceHubSelector._order_item(order) for order in self._trainer_orders(trainer=trainer, customer=customer)[:30]]

    @staticmethod
    def _access_history(*, customer) -> list[dict[str, Any]]:
        qs = Entitlement.objects.filter(user=customer).order_by("-created_at")[:40]
        return [
            {
                "id": str(item.id),
                "source_type": item.source_type,
                "source_order_id": _uuid(item.source_order_id),
                "source_subscription_id": _uuid(item.source_subscription_id),
                "target_type": item.target_type,
                "target_id": _uuid(item.target_id),
                "status": item.status,
                "starts_at": _iso(item.starts_at),
                "ends_at": _iso(item.ends_at),
                "created_at": _iso(item.created_at),
                "metadata": item.metadata or {},
            }
            for item in qs
        ]

    @staticmethod
    def _attendance_history(*, trainer, customer) -> list[dict[str, Any]]:
        try:
            from apps.booking.models import BookingAttendance, SessionReservation
        except Exception:
            return []
        attendance_rows = (
            BookingAttendance.objects
            .select_related("reservation", "reservation__slot")
            .filter(trainer=trainer, customer=customer)
            .order_by("-created_at")[:30]
        )
        if attendance_rows:
            return [
                {
                    "id": str(row.id),
                    "status": row.status,
                    "title": row.reservation.title,
                    "notes": row.reservation.notes,
                    "starts_at": _iso(row.reservation.slot.starts_at),
                    "ends_at": _iso(row.reservation.slot.ends_at),
                    "checked_in_at": _iso(row.checked_in_at),
                    "checked_out_at": _iso(row.checked_out_at),
                    "duration_seconds": row.duration_seconds,
                    "created_at": _iso(row.created_at),
                }
                for row in attendance_rows
            ]
        rows = (
            SessionReservation.objects
            .select_related("slot")
            .filter(trainer=trainer, customer=customer)
            .order_by("-created_at")[:30]
        )
        return [
            {
                "id": str(row.id),
                "status": row.status,
                "title": row.title,
                "notes": row.notes,
                "starts_at": _iso(row.slot.starts_at),
                "ends_at": _iso(row.slot.ends_at),
                "created_at": _iso(row.created_at),
            }
            for row in rows
        ]

    @staticmethod
    def _notes(*, trainer, customer) -> list[dict[str, Any]]:
        return [
            {
                "id": str(note.id),
                "body": note.body,
                "visibility": note.visibility,
                "pinned": note.pinned,
                "created_at": _iso(note.created_at),
                "updated_at": _iso(note.updated_at),
            }
            for note in CustomerNote.objects.filter(trainer=trainer, customer=customer)[:30]
        ]

    @staticmethod
    def _segments(*, trainer, customer=None) -> list[dict[str, Any]]:
        qs = CustomerSegment.objects.filter(trainer=trainer).annotate(customers_count=Count("customers"))
        if customer is not None:
            profile, _ = CustomerProfile.objects.get_or_create(user=customer, defaults={"display_name": customer.email})
            qs = qs.filter(customers=profile)
        return [
            {
                "id": str(segment.id),
                "name": segment.name,
                "description": segment.description,
                "color": segment.color,
                "customers_count": segment.customers_count,
            }
            for segment in qs.order_by("name")
        ]
