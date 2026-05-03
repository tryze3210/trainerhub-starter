from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.events.services import DomainEventService
from apps.orders.services import OrderService
from apps.payments.models import PaymentWebhookEvent
from apps.payments.services import PaymentService


@pytest.mark.django_db
def test_admin_can_open_outbox_entity_detail():
    admin = get_user_model().objects.create_superuser(email='entity-admin@example.com', password='pass12345')
    emitted = DomainEventService().emit(
        event_type='payment.succeeded',
        aggregate_type='payment',
        aggregate_id='pay-entity-001',
        payload={'amount': '100.00'},
        idempotency_key='entity-detail-test',
    )

    client = APIClient()
    client.force_authenticate(user=admin)
    response = client.get(f"/api/v1/ops/admin/entities/outbox_message/{emitted['outbox_message_id']}/")

    assert response.status_code == 200
    payload = response.json()
    assert payload['entity_type'] == 'outbox_message'
    assert payload['status'] in {'pending', 'failed', 'processed', 'dead'}
    assert any(item['entity_type'] == 'domain_event' for item in payload['relationships'])


@pytest.mark.django_db
def test_admin_can_open_payment_webhook_entity_detail(user_factory):
    admin = get_user_model().objects.create_superuser(email='webhook-entity-admin@example.com', password='pass12345')
    user = user_factory(email='buyer-entity@example.com')
    order = OrderService.create_one_time_order(
        user=user,
        item_type='video',
        item_id='entity-video-1',
        title='Entity Video',
        amount=Decimal('199.00'),
    )
    payment = PaymentService.create_checkout_payment(order=order)
    webhook = PaymentWebhookEvent.objects.create(
        provider='mock',
        event_type='payment.succeeded',
        external_event_id='entity-webhook-001',
        payment=payment,
        status=PaymentWebhookEvent.Status.PROCESSED,
        payload={'external_payment_id': payment.external_payment_id},
    )

    client = APIClient()
    client.force_authenticate(user=admin)
    response = client.get(f'/api/v1/ops/admin/entities/payment_webhook/{webhook.id}/')

    assert response.status_code == 200
    payload = response.json()
    assert payload['entity_type'] == 'payment_webhook'
    assert payload['primary']['payment_id'] == str(payment.id)
    assert any(item['entity_type'] == 'payment' for item in payload['relationships'])
