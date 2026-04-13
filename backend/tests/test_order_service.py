from apps.orders.models import Order
from apps.orders.services import OrderService


def test_create_or_reuse_pending_order(user_factory):
    user = user_factory()
    order = OrderService.create_or_reuse_pending_order(user=user, item_type=Order.ItemType.VIDEO, item_id='101')
    same_order = OrderService.create_or_reuse_pending_order(user=user, item_type=Order.ItemType.VIDEO, item_id='101')
    assert order.id == same_order.id
