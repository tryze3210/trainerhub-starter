from apps.billing.models import CheckoutSession


def list_checkout_sessions_for_user(user):
    return CheckoutSession.objects.filter(user=user).order_by('-created_at')
