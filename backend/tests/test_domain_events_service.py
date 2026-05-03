import pytest

from apps.events.models import DomainEvent, OutboxMessage
from apps.events.services import DomainEventService, emit_event


@pytest.mark.django_db
def test_domain_event_emit_persists_outbox_and_is_idempotent():
    service = DomainEventService()

    first = service.emit(
        event_type='payments.payment_paid',
        aggregate_type='payment',
        aggregate_id='payment-1',
        payload={'order_id': 'order-1'},
        idempotency_key='payment-1:succeeded',
    )
    second = service.emit(
        event_type='payments.payment_paid',
        aggregate_type='payment',
        aggregate_id='payment-1',
        payload={'order_id': 'order-1'},
        idempotency_key='payment-1:succeeded',
    )

    assert first['event_id'] == second['event_id']
    assert first['outbox_message_id'] == second['outbox_message_id']
    assert second['status'] == 'duplicate_accepted'
    assert DomainEvent.objects.count() == 1
    assert OutboxMessage.objects.count() == 1
    assert OutboxMessage.objects.get().status == OutboxMessage.Status.PENDING


@pytest.mark.django_db
def test_outbox_dispatch_marks_pending_messages_processed():
    service = DomainEventService()
    service.emit(
        event_type='entitlements.granted',
        aggregate_type='entitlement',
        aggregate_id='entitlement-1',
        payload={'user_id': 'user-1'},
    )

    result = service.dispatch_pending_batch(batch_size=10)

    assert result == {'claimed': 1, 'processed': 1, 'failed': 0}
    assert OutboxMessage.objects.get().status == OutboxMessage.Status.PROCESSED


@pytest.mark.django_db
def test_legacy_emit_event_facade_still_returns_event_name():
    payload = emit_event(
        event_name='legacy.event',
        aggregate_type='legacy',
        aggregate_id='legacy-1',
        payload={'ok': True},
    )

    assert payload['event_name'] == 'legacy.event'
    assert payload['event_type'] == 'legacy.event'
    assert DomainEvent.objects.count() == 1
    assert OutboxMessage.objects.count() == 1
