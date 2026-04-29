from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

from django.db.models import Q

from apps.orders.models import Order, OrderItem, OrderStatus, OrderType, PurchasedItemType
from apps.subscriptions.models import SubscriptionPlan


@dataclass(frozen=True)
class CheckoutItemSnapshot:
    item_type: str
    item_id: str
    title: str
    amount: Decimal
    currency: str
    metadata: dict[str, Any]


def _uuid_or_none(value: Any) -> UUID | None:
    try:
        return UUID(str(value))
    except Exception:
        return None


def _is_intish(value: Any) -> bool:
    return str(value).isdigit()


class CheckoutCatalogResolver:
    @staticmethod
    def resolve_one_time_item(*, item_type: str, item_id: Any, title: str | None = None, amount: Decimal | None = None, currency: str = 'RUB') -> CheckoutItemSnapshot:
        from apps.content.models import PublishedBundle, PublishedProgram, PublishedVideo

        item_type = str(item_type)
        model_map = {
            PurchasedItemType.VIDEO: PublishedVideo,
            PurchasedItemType.PROGRAM: PublishedProgram,
            PurchasedItemType.BUNDLE: PublishedBundle,
            'video': PublishedVideo,
            'program': PublishedProgram,
            'bundle': PublishedBundle,
        }
        model = model_map.get(item_type)
        if not model:
            raise ValueError('Unsupported checkout item_type.')

        lookup = Q(slug=str(item_id))
        uuid_value = _uuid_or_none(item_id)
        if uuid_value:
            lookup = lookup | Q(source_draft_id=uuid_value)
        if _is_intish(item_id):
            lookup = lookup | Q(id=int(str(item_id)))

        obj = model.objects.select_related('trainer_profile').filter(lookup, is_active=True).first()
        if obj:
            if getattr(obj, 'visibility', 'public') != 'public':
                raise ValueError('This item is not available for public checkout.')

            trainer_profile = getattr(obj, 'trainer_profile', None)
            price = getattr(obj, 'price_amount', None)
            resolved_amount = Decimal(str(price if price is not None else amount or Decimal('0.00'))).quantize(Decimal('0.01'))
            if resolved_amount < Decimal('0.00'):
                raise ValueError('Checkout amount cannot be negative.')

            return CheckoutItemSnapshot(
                item_type=item_type,
                item_id=str(obj.source_draft_id),
                title=obj.title or title or 'Content access',
                amount=resolved_amount,
                currency=getattr(obj, 'currency', '') or currency or 'RUB',
                metadata={
                    'published_id': str(obj.id),
                    'source_draft_id': str(obj.source_draft_id),
                    'slug': obj.slug,
                    'trainer_id': str(getattr(trainer_profile, 'user_id', '') or ''),
                    'trainer_profile_id': str(getattr(trainer_profile, 'id', '') or ''),
                    'trainer_name': getattr(trainer_profile, 'display_name', ''),
                    'title': obj.title,
                    'price_source': 'catalog',
                },
            )

        # Compatibility path for service-level unit tests and admin/manual order creation.
        # Public API checkout should normally resolve catalog rows, but internal callers may
        # create orders from a trusted explicit title/amount pair before catalog publication.
        if title is not None and amount is not None:
            resolved_amount = Decimal(str(amount)).quantize(Decimal('0.01'))
            if resolved_amount < Decimal('0.00'):
                raise ValueError('Checkout amount cannot be negative.')
            return CheckoutItemSnapshot(
                item_type=item_type,
                item_id=str(item_id),
                title=title or 'Content access',
                amount=resolved_amount,
                currency=currency or 'RUB',
                metadata={
                    'source_draft_id': str(item_id),
                    'title': title or 'Content access',
                    'price_source': 'explicit',
                },
            )

        raise ValueError('Published checkout item was not found or is inactive.')


class OrderService:
    @staticmethod
    def create_one_time_order(*, user, item_type: str, item_id, title: str | None = None, amount: Decimal | None = None, currency: str = 'RUB') -> Order:
        snapshot = CheckoutCatalogResolver.resolve_one_time_item(
            item_type=item_type,
            item_id=item_id,
            title=title,
            amount=amount,
            currency=currency,
        )
        order = Order.objects.create(
            user=user,
            order_type=OrderType.ONE_TIME,
            status=OrderStatus.AWAITING_PAYMENT,
            total_amount=snapshot.amount,
            currency=snapshot.currency,
        )
        OrderItem.objects.create(
            order=order,
            item_type=snapshot.item_type,
            item_id=snapshot.item_id,
            title_snapshot=snapshot.title,
            quantity=1,
            unit_price=snapshot.amount,
            total_price=snapshot.amount,
            metadata=snapshot.metadata,
        )
        return order

    @staticmethod
    def create_or_reuse_pending_order(*, user, item_type: str, item_id, title: str | None = None, amount: Decimal | None = None, currency: str = 'RUB') -> Order:
        item_type = str(item_type)
        item_id_text = str(item_id)
        existing = (
            Order.objects.filter(
                user=user,
                order_type=OrderType.ONE_TIME,
                status__in=[OrderStatus.PENDING, OrderStatus.AWAITING_PAYMENT],
                items__item_type=item_type,
                items__item_id=item_id_text,
            )
            .order_by('-created_at')
            .first()
        )
        if existing:
            return existing
        return OrderService.create_one_time_order(
            user=user,
            item_type=item_type,
            item_id=item_id_text,
            title=title or f'{item_type.title()} access',
            amount=amount if amount is not None else Decimal('0.00'),
            currency=currency,
        )

    @staticmethod
    def create_subscription_order(*, user, plan: SubscriptionPlan) -> Order:
        order = Order.objects.create(
            user=user,
            order_type=OrderType.SUBSCRIPTION,
            status=OrderStatus.AWAITING_PAYMENT,
            total_amount=plan.price,
            currency=plan.currency,
        )
        OrderItem.objects.create(
            order=order,
            item_type=PurchasedItemType.SUBSCRIPTION_PLAN,
            item_id=str(plan.id),
            title_snapshot=plan.title,
            quantity=1,
            unit_price=plan.price,
            total_price=plan.price,
            metadata={'plan_code': plan.code, 'title': plan.title, 'trainer_id': getattr(plan, 'trainer_id', '')},
        )
        return order
