from datetime import timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.notifications.domain.triggers import DomainNotificationTriggers
from apps.notifications.models import Notification, NotificationDelivery, NotificationStatus, NotificationType


@pytest.mark.django_db
def test_v91_domain_notification_triggers_create_business_events_idempotently():
    user = get_user_model().objects.create_user(email='v91-notify@example.com', password='pass12345')
    now = timezone.now()
    payment = SimpleNamespace(id=uuid4(), order_id=uuid4(), amount='1290.00', currency='RUB')
    entitlement = SimpleNamespace(id=uuid4(), target_type='course', target_id=uuid4())
    subscription = SimpleNamespace(id=uuid4(), ends_at=now + timedelta(days=3))
    payout = SimpleNamespace(id=uuid4(), amount='950.00', currency='RUB')

    triggers = DomainNotificationTriggers()
    triggers.on_payment_succeeded(user=user, payment=payment)
    triggers.on_payment_refunded(user=user, payment=payment, refund_id='rf_v91', refund_kind='partial', amount='250.00')
    triggers.on_access_granted(user=user, entitlement=entitlement)
    triggers.on_subscription_expiring(user=user, subscription=subscription, days_left=3)
    triggers.on_payout_paid(user=user, payout=payout)

    assert set(Notification.objects.filter(user=user).values_list('notification_type', flat=True)) == {
        NotificationType.PAYMENT,
        NotificationType.SYSTEM,
        NotificationType.SUBSCRIPTION,
    }
    assert set(NotificationDelivery.objects.filter(user=user).values_list('type', flat=True)) == {
        NotificationType.PAYMENT_SUCCEEDED,
        NotificationType.PAYMENT_REFUNDED,
        NotificationType.ACCESS_GRANTED,
        NotificationType.SUBSCRIPTION_EXPIRING,
        NotificationType.PAYOUT_PAID,
    }
    assert NotificationDelivery.objects.filter(user=user, status=NotificationStatus.SKIPPED).count() == 5

    triggers.on_payment_succeeded(user=user, payment=payment)
    triggers.on_access_granted(user=user, entitlement=entitlement)

    assert Notification.objects.filter(user=user, metadata__event_key=f'payment:{payment.id}:succeeded').count() == 1
    assert Notification.objects.filter(user=user, metadata__event_key=f'entitlement:{entitlement.id}:granted').count() == 1
    assert NotificationDelivery.objects.filter(user=user, type=NotificationType.PAYMENT_SUCCEEDED).count() == 1
    assert NotificationDelivery.objects.filter(user=user, type=NotificationType.ACCESS_GRANTED).count() == 1


def test_v91_pending_email_sweep_is_scheduled_in_celery_beat():
    from config.celery import app

    schedule = app.conf.beat_schedule
    assert schedule['trainerhub-notifications-sweep-pending-email']['task'] == (
        'apps.notifications.tasks.sweep_pending_email_notifications'
    )
    assert schedule['trainerhub-notifications-sweep-pending-email']['options']['queue'] == 'email'
