from django.utils import timezone
from apps.subscriptions.models import Subscription, SubscriptionPlan


def list_active_plans():
    return SubscriptionPlan.objects.filter(is_active=True).order_by('trainer_id', 'price')


def get_active_subscription_for_user(user):
    now = timezone.now()
    return Subscription.objects.filter(
        user=user,
        status=Subscription.Status.ACTIVE,
        current_period_starts_at__lte=now,
        current_period_ends_at__gt=now,
    ).select_related('plan').first()
