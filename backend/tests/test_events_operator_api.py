import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.events.models import OutboxMessage
from apps.events.services import DomainEventService


@pytest.fixture
def admin_client():
    user = get_user_model().objects.create_superuser(
        email='events-admin@example.com',
        password='pass12345',
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_operator_can_filter_events_and_outbox(admin_client):
    service = DomainEventService()
    emitted = service.emit(
        event_type='payment.succeeded',
        aggregate_type='payment',
        aggregate_id='pay_001',
        payload={'amount': '49.00'},
        idempotency_key='payment:pay_001:succeeded',
    )

    events_response = admin_client.get('/api/v1/events/', {'event_type': 'payment.succeeded'})
    assert events_response.status_code == 200
    assert events_response.json()[0]['id'] == emitted['event_id']

    outbox_response = admin_client.get('/api/v1/events/outbox/', {'status': 'pending'})
    assert outbox_response.status_code == 200
    assert outbox_response.json()[0]['event_type'] == 'payment.succeeded'


@pytest.mark.django_db
def test_operator_can_retry_dead_outbox_message(admin_client):
    emitted = DomainEventService().emit(
        event_type='entitlement.granted',
        aggregate_type='entitlement',
        aggregate_id='ent_001',
        payload={'target_type': 'video'},
        idempotency_key='entitlement:ent_001:granted',
    )
    message = OutboxMessage.objects.get(pk=emitted['outbox_message_id'])
    message.status = OutboxMessage.Status.DEAD
    message.attempts = message.max_attempts
    message.last_error = 'provider unavailable'
    message.save(update_fields=['status', 'attempts', 'last_error', 'updated_at'])

    response = admin_client.post(
        f'/api/v1/events/outbox/{message.id}/retry/',
        {'reset_attempts': True},
        format='json',
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload['status'] == 'pending'
    assert payload['attempts'] == 0
    assert payload['last_error'] == ''


@pytest.mark.django_db
def test_operator_can_requeue_stuck_processing_messages(admin_client):
    emitted = DomainEventService().emit(
        event_type='notification.requested',
        aggregate_type='notification',
        aggregate_id='notice_001',
        payload={'channel': 'email'},
        idempotency_key='notification:notice_001:requested',
    )
    message = OutboxMessage.objects.get(pk=emitted['outbox_message_id'])
    message.status = OutboxMessage.Status.PROCESSING
    message.locked_at = timezone.now() - timezone.timedelta(minutes=30)
    message.save(update_fields=['status', 'locked_at', 'updated_at'])

    response = admin_client.post(
        '/api/v1/events/outbox/requeue-stuck/',
        {'older_than_minutes': 15},
        format='json',
    )

    assert response.status_code == 202
    assert response.json()['requeued'] == 1
    message.refresh_from_db()
    assert message.status == OutboxMessage.Status.PENDING
    assert message.locked_at is None
