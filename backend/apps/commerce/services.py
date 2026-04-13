from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from apps.entitlements.models import Entitlement, EntitlementSourceType, EntitlementTargetType
from apps.orders.models import Order, OrderStatus, PurchasedItemType
from apps.subscriptions.models import Subscription, SubscriptionStatus, SubscriptionPlan


class CommerceFinalizationService:
    @staticmethod
    @transaction.atomic
    def finalize_paid_order(*, order: Order) -> None:
        if order.status not in [OrderStatus.PAID, OrderStatus.COMPLETED]:
            raise ValueError('Order must be paid before finalization')

        first_item = order.items.first()
        if not first_item:
            raise ValueError('Order must contain at least one item')

        if first_item.item_type == PurchasedItemType.SUBSCRIPTION_PLAN:
            plan = SubscriptionPlan.objects.get(id=first_item.item_id)
            subscription = Subscription.objects.create(
                user=order.user,
                plan=plan,
                source_order=order,
                status=SubscriptionStatus.ACTIVE,
                starts_at=timezone.now(),
                ends_at=timezone.now() + timedelta(days=plan.period_days),
                auto_renew=False,
            )
            Entitlement.objects.create(
                user=order.user,
                source_type=EntitlementSourceType.SUBSCRIPTION,
                source_subscription=subscription,
                target_type=EntitlementTargetType.LIBRARY,
                target_id=None,
                starts_at=subscription.starts_at,
                ends_at=subscription.ends_at,
                metadata={'plan_code': plan.code},
            )
        else:
            Entitlement.objects.create(
                user=order.user,
                source_type=EntitlementSourceType.ORDER,
                source_order=order,
                target_type=first_item.item_type,
                target_id=first_item.item_id,
                starts_at=timezone.now(),
                metadata={'title': first_item.title_snapshot},
            )

        order.status = OrderStatus.COMPLETED
        order.completed_at = timezone.now()
        order.save(update_fields=['status', 'completed_at', 'updated_at'])
