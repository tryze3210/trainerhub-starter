from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.entitlements.models import Entitlement, EntitlementSourceType, EntitlementStatus, EntitlementTargetType
from apps.entitlements.services import EntitlementService
from apps.events.services import DomainEventService
from apps.orders.models import Order, OrderStatus, PurchasedItemType
from apps.subscriptions.models import Subscription, SubscriptionStatus, SubscriptionPlan


class CommerceFinalizationService:
    @staticmethod
    def _has_active_access_for_order(order: Order) -> bool:
        if order.granted_entitlements.filter(status=EntitlementStatus.ACTIVE).exists():
            return True
        return Entitlement.objects.filter(
            status=EntitlementStatus.ACTIVE,
            source_subscription__source_order=order,
        ).exists()

    @staticmethod
    def _emit_order_completed(*, order: Order, payment=None) -> None:
        DomainEventService().emit(
            event_type='order.completed',
            aggregate_type='order',
            aggregate_id=str(order.id),
            idempotency_key=f'order:{order.id}:completed',
            payload={
                'order_id': str(order.id),
                'payment_id': str(payment.id) if payment else '',
                'user_id': str(order.user_id),
                'order_type': order.order_type,
                'status': order.status,
                'currency': order.currency,
                'total_amount': str(order.total_amount),
                'completed_at': order.completed_at.isoformat() if order.completed_at else None,
            },
        )

    @staticmethod
    def _emit_entitlement_granted(*, entitlement, order: Order, payment=None, first_item=None) -> None:
        DomainEventService().emit(
            event_type='entitlement.granted',
            aggregate_type='entitlement',
            aggregate_id=str(entitlement.id),
            idempotency_key=f'entitlement:{entitlement.id}:granted',
            payload={
                'entitlement_id': str(entitlement.id),
                'user_id': str(entitlement.user_id),
                'order_id': str(order.id),
                'payment_id': str(payment.id) if payment else '',
                'source_type': entitlement.source_type,
                'target_type': entitlement.target_type,
                'target_id': str(entitlement.target_id or ''),
                'status': entitlement.status,
                'item_type': getattr(first_item, 'item_type', ''),
                'item_id': str(getattr(first_item, 'item_id', '') or ''),
            },
        )

    @staticmethod
    def _emit_subscription_activated(*, subscription: Subscription, order: Order, payment=None, plan=None) -> None:
        DomainEventService().emit(
            event_type='subscription.activated',
            aggregate_type='subscription',
            aggregate_id=str(subscription.id),
            idempotency_key=f'subscription:{subscription.id}:activated',
            payload={
                'subscription_id': str(subscription.id),
                'user_id': str(subscription.user_id),
                'order_id': str(order.id),
                'payment_id': str(payment.id) if payment else '',
                'plan_id': str(subscription.plan_id),
                'plan_code': getattr(plan or subscription.plan, 'code', ''),
                'status': subscription.status,
                'starts_at': subscription.starts_at.isoformat() if subscription.starts_at else None,
                'ends_at': subscription.ends_at.isoformat() if subscription.ends_at else None,
            },
        )

    @staticmethod
    @transaction.atomic
    def finalize_paid_order(*, order: Order, payment=None) -> None:
        order = Order.objects.select_for_update().prefetch_related('items').get(pk=order.pk)
        if order.status == OrderStatus.COMPLETED and CommerceFinalizationService._has_active_access_for_order(order):
            return
        if order.status not in [OrderStatus.PAID, OrderStatus.COMPLETED]:
            raise ValueError('Order must be paid before finalization')

        first_item = order.items.order_by('created_at').first()
        if not first_item:
            raise ValueError('Order must contain at least one item')

        now = timezone.now()
        metadata = first_item.metadata or {}
        if payment:
            metadata = {**metadata, 'payment_id': str(payment.id), 'payment_provider': payment.provider}

        if first_item.item_type == PurchasedItemType.SUBSCRIPTION_PLAN:
            plan = SubscriptionPlan.objects.get(id=first_item.item_id)
            subscription, _ = Subscription.objects.update_or_create(
                user=order.user,
                source_order=order,
                defaults={
                    'plan': plan,
                    'status': SubscriptionStatus.ACTIVE,
                    'starts_at': now,
                    'ends_at': now + timedelta(days=plan.period_days),
                    'auto_renew': False,
                },
            )
            entitlement = EntitlementService.grant(
                user=order.user,
                source_type=EntitlementSourceType.SUBSCRIPTION,
                source_subscription=subscription,
                target_type=EntitlementTargetType.LIBRARY,
                target_id=None,
                starts_at=subscription.starts_at,
                ends_at=subscription.ends_at,
                metadata={'plan_code': plan.code, 'title': plan.title, **metadata},
            )
            CommerceFinalizationService._emit_subscription_activated(subscription=subscription, order=order, payment=payment, plan=plan)
            CommerceFinalizationService._emit_entitlement_granted(entitlement=entitlement, order=order, payment=payment, first_item=first_item)
        else:
            entitlement = EntitlementService.grant(
                user=order.user,
                source_type=EntitlementSourceType.ORDER,
                source_order=order,
                target_type=first_item.item_type,
                target_id=first_item.item_id,
                starts_at=now,
                metadata={
                    'title': first_item.title_snapshot,
                    'trainer_id': metadata.get('trainer_id', ''),
                    'trainer_name': metadata.get('trainer_name', ''),
                    'slug': metadata.get('slug', ''),
                    'published_id': metadata.get('published_id', ''),
                    **metadata,
                },
            )
            CommerceFinalizationService._emit_entitlement_granted(entitlement=entitlement, order=order, payment=payment, first_item=first_item)

        order.status = OrderStatus.COMPLETED
        order.completed_at = order.completed_at or now
        order.save(update_fields=['status', 'completed_at', 'updated_at'])
        CommerceFinalizationService._emit_order_completed(order=order, payment=payment)
