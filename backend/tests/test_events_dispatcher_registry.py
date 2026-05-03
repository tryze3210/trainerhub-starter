import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.events.models import InboxMessage, OutboxMessage
from apps.events.services import DomainEventService


@pytest.mark.django_db
def test_default_dispatcher_records_projection_inbox_and_marks_outbox_processed():
    service = DomainEventService()
    emitted = service.emit(
        event_type='payment.succeeded',
        aggregate_type='payment',
        aggregate_id='pay_dispatch_001',
        payload={'amount': '49.00'},
        idempotency_key='payment:pay_dispatch_001:succeeded',
    )

    result = service.dispatch_pending_batch(batch_size=10)

    assert result['claimed'] == 1
    assert result['processed'] == 1
    assert result['failed'] == 0

    message = OutboxMessage.objects.get(pk=emitted['outbox_message_id'])
    assert message.status == OutboxMessage.Status.PROCESSED
    assert message.processed_at is not None

    consumers = set(
        InboxMessage.objects.filter(
            message_key=emitted['event_id'],
            status=InboxMessage.Status.PROCESSED,
        ).values_list('consumer', flat=True)
    )
    assert 'events.payment_projection' in consumers
    assert 'events.audit_projection' in consumers
    assert 'analytics.commerce_projection' in consumers
    assert 'notifications.event_projection' in consumers
    assert 'payouts.revenue_projection' in consumers

    initial_projection_count = InboxMessage.objects.filter(message_key=emitted['event_id']).count()

    second_result = service.dispatch_pending_batch(batch_size=10)
    assert second_result['claimed'] == 0
    assert InboxMessage.objects.filter(message_key=emitted['event_id']).count() == initial_projection_count


@pytest.mark.django_db
def test_operator_can_list_registered_event_handlers():
    admin = get_user_model().objects.create_superuser(
        email='dispatch-admin@example.com',
        password='pass12345',
    )
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get('/api/v1/events/handlers/')

    assert response.status_code == 200
    payload = response.json()
    assert any(item['consumer'] == 'events.payment_projection' for item in payload)
    assert any(item['consumer'] == 'events.audit_projection' for item in payload)
    assert any(item['consumer'] == 'analytics.commerce_projection' for item in payload)
    assert any(item['consumer'] == 'notifications.event_projection' for item in payload)
    assert any(item['consumer'] == 'payouts.revenue_projection' for item in payload)
