from decimal import Decimal
from apps.orders.models import Order, OrderItem, OrderStatus, OrderType, PurchasedItemType
from apps.subscriptions.models import SubscriptionPlan


class OrderService:
    @staticmethod
    def create_one_time_order(*, user, item_type: str, item_id, title: str, amount: Decimal, currency: str = 'RUB') -> Order:
        order = Order.objects.create(
            user=user,
            order_type=OrderType.ONE_TIME,
            status=OrderStatus.AWAITING_PAYMENT,
            total_amount=amount,
            currency=currency,
        )
        OrderItem.objects.create(
            order=order,
            item_type=item_type,
            item_id=item_id,
            title_snapshot=title,
            quantity=1,
            unit_price=amount,
            total_price=amount,
        )
        return order

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
            item_id=plan.id,
            title_snapshot=plan.title,
            quantity=1,
            unit_price=plan.price,
            total_price=plan.price,
            metadata={'plan_code': plan.code},
        )
        return order
