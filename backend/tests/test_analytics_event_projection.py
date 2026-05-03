from __future__ import annotations

from uuid import uuid4

import pytest
from rest_framework.test import APIClient

from apps.analytics.models import AnalyticsEvent
from apps.analytics.projections import ANALYTICS_PROJECTION_CONSUMER, analytics_projection_service
from apps.events.models import InboxMessage
from apps.events.services import DomainEventService
from apps.users.models import User


@pytest.mark.django_db
def test_payment_success_event_projects_to_analytics_event_once():
    user_id = uuid4()
    trainer_id = uuid4()
    order_id = uuid4()
    event = DomainEventService().emit(
        event_type='payment.succeeded',
        aggregate_type='payment',
        aggregate_id='pay_001',
        idempotency_key='payment:pay_001:succeeded',
        payload={
            'amount': '49.00',
            'currency': 'EUR',
            'user_id': str(user_id),
            'trainer_id': str(trainer_id),
            'order_id': str(order_id),
            'session_id': 'sess_001',
            'utm_source': 'telegram',
        },
    )

    result = DomainEventService().dispatch_pending_batch(batch_size=10)

    assert result['processed'] == 1
    analytics_event = AnalyticsEvent.objects.get(event_uuid=event['event_id'])
    assert analytics_event.event_name == AnalyticsEvent.EVENT_PURCHASE_COMPLETED
    assert analytics_event.session_id == 'sess_001'
    assert analytics_event.user_id == user_id
    assert analytics_event.trainer_id == trainer_id
    assert analytics_event.order_id == order_id
    assert analytics_event.metadata['source'] == 'domain_event_outbox'
    assert analytics_event.metadata['amount'] == '49.00'
    assert InboxMessage.objects.filter(consumer=ANALYTICS_PROJECTION_CONSUMER).count() == 1

    # Manual replay of the same envelope must not create a duplicate row.
    outbox_payload = analytics_event.metadata['domain_payload']
    assert outbox_payload['amount'] == '49.00'
    message = InboxMessage.objects.get(consumer=ANALYTICS_PROJECTION_CONSUMER)
    replay = analytics_projection_service.project_outbox_payload(
        topic='payment.succeeded',
        payload=message.payload['event'],
    )
    assert replay['status'] == 'projected'
    assert AnalyticsEvent.objects.filter(event_uuid=event['event_id']).count() == 1


@pytest.mark.django_db
def test_unmapped_domain_event_is_marked_as_skipped_projection():
    event = DomainEventService().emit(
        event_type='payout.accrued',
        aggregate_type='payout',
        aggregate_id='payout_001',
        idempotency_key='payout:payout_001:accrued',
        payload={'amount': '15.00'},
    )

    result = DomainEventService().dispatch_pending_batch(batch_size=10)

    assert result['processed'] == 1
    assert AnalyticsEvent.objects.filter(event_uuid=event['event_id']).count() == 0
    inbox = InboxMessage.objects.get(consumer=ANALYTICS_PROJECTION_CONSUMER)
    assert inbox.payload['projection_status'] == 'skipped'


@pytest.mark.django_db
def test_analytics_projection_health_api_is_admin_only():
    admin = User.objects.create_superuser(email='admin@example.com', password='pass12345')
    DomainEventService().emit(
        event_type='checkout.started',
        aggregate_type='checkout',
        aggregate_id='checkout_001',
        idempotency_key='checkout:checkout_001:started',
        payload={'session_id': 'sess_checkout'},
    )
    DomainEventService().dispatch_pending_batch(batch_size=10)

    client = APIClient()
    client.force_authenticate(user=admin)
    response = client.get('/api/v1/analytics/events/projection-health/')

    assert response.status_code == 200
    payload = response.json()
    assert payload['consumer'] == ANALYTICS_PROJECTION_CONSUMER
    assert payload['status'] == 'ok'
    assert payload['projected_messages'] >= 1
