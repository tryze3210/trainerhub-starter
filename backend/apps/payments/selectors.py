from apps.payments.models import Payment


def list_payments_for_user(user):
    return Payment.objects.filter(user=user).order_by('-created_at')


def list_all_payments():
    return Payment.objects.all().order_by('-created_at')
