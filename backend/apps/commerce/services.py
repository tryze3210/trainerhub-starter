from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.entitlements.models import EntitlementSourceType, EntitlementTargetType
from apps.entitlements.services import EntitlementService
from apps.orders.models import Order, OrderStatus, PurchasedItemType
from apps.subscriptions.models import Subscription, SubscriptionStatus, SubscriptionPlan


class CommerceFinalizationService:
    @staticmethod
    @transaction.atomic
    def finalize_paid_order(*, order: Order, payment=None) -> None:
        order = Order.objects.select_for_update().prefetch_related('items').get(pk=order.pk)
        if order.status == OrderStatus.COMPLETED:
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
            EntitlementService.grant(
                user=order.user,
                source_type=EntitlementSourceType.SUBSCRIPTION,
                source_subscription=subscription,
                target_type=EntitlementTargetType.LIBRARY,
                target_id=None,
                starts_at=subscription.starts_at,
                ends_at=subscription.ends_at,
                metadata={'plan_code': plan.code, 'title': plan.title, **metadata},
            )
        else:
            EntitlementService.grant(
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

        order.status = OrderStatus.COMPLETED
        order.completed_at = now
        order.save(update_fields=['status', 'completed_at', 'updated_at'])
