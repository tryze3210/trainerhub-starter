from apps.orders.models import Order
from apps.entitlements.selectors import get_user_active_entitlements


def get_user_orders(*, user):
    return Order.objects.filter(user=user).order_by('-created_at')


def get_user_content_library(*, user):
    return get_user_active_entitlements(user=user).order_by('-created_at')
