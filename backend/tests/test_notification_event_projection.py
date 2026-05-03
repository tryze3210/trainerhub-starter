import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.events.models import InboxMessage, OutboxMessage
from apps.events.services import DomainEventService
from apps.notifications.models import Notification, NotificationType
from apps.notifications.projections import NOTIFICATION_PROJECTION_CONSUMER


@pytest.mark.django_db
def test_payment_success_event_creates_idempotent_user_notification():
    user = get_user_model().objects.create_user(email='buyer-notify@example.com', password='pass12345')
    service = DomainEventService()
    emitted = service.emit(
        event_type='payment.succeeded',
        aggregate_type='payment',
        aggregate_id='pay_notify_001',
        payload={
            'user_id': str(user.id),
            'payment_id': 'pay_notify_001',
            'order_id': 'order_notify_001',
            'amount': '499.00',
            'currency': 'RUB',
        },
        idempotency_key='payment:pay_notify_001:succeeded',
    )

    result = service.dispatch_pending_batch(batch_size=10)

    assert result['claimed'] == 1
    assert result['processed'] == 1
    assert Notification.objects.filter(
        user=user,
        notification_type=NotificationType.PAYMENT,
        metadata__domain_event_id=emitted['event_id'],
    ).count() == 1

    inbox = InboxMessage.objects.get(
        consumer=NOTIFICATION_PROJECTION_CONSUMER,
        message_key=emitted['event_id'],
    )
    assert inbox.status == InboxMessage.Status.PROCESSED
    assert inbox.payload['projection_status'] == 'projected'
    assert inbox.payload['recipient_user_ids'] == [str(user.id)]

    OutboxMessage.objects.filter(pk=emitted['outbox_message_id']).update(status=OutboxMessage.Status.PENDING)
    second_result = service.dispatch_pending_batch(batch_size=10)

    assert second_result['claimed'] == 1
    assert second_result['processed'] == 1
    assert Notification.objects.filter(
        user=user,
        notification_type=NotificationType.PAYMENT,
        metadata__domain_event_id=emitted['event_id'],
    ).count() == 1


@pytest.mark.django_db
def test_notification_projection_records_skip_without_recipient():
    service = DomainEventService()
    emitted = service.emit(
        event_type='entitlement.granted',
        aggregate_type='entitlement',
        aggregate_id='ent_no_recipient_001',
        payload={'target_type': 'video'},
        idempotency_key='entitlement:ent_no_recipient_001:granted',
    )

    result = service.dispatch_pending_batch(batch_size=10)

    assert result['processed'] == 1
    inbox = InboxMessage.objects.get(
        consumer=NOTIFICATION_PROJECTION_CONSUMER,
        message_key=emitted['event_id'],
    )
    assert inbox.payload['projection_status'] == 'skipped'
    assert 'recipient' in inbox.payload['reason'].lower()
    assert Notification.objects.count() == 0


@pytest.mark.django_db
def test_admin_can_read_notification_projection_health():
    admin = get_user_model().objects.create_superuser(email='notify-admin@example.com', password='pass12345')
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get('/api/v1/notifications/admin/projection-health/')

    assert response.status_code == 200
    payload = response.json()
    assert payload['consumer'] == NOTIFICATION_PROJECTION_CONSUMER
    assert 'created_notifications' in payload
