from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.orders.checkout_integrity import CheckoutIntegrityService
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment


@pytest.mark.django_db
def test_checkout_one_time_is_idempotent_and_stores_price_commission_snapshot():
    user = get_user_model().objects.create_user(email='buyer-integrity@example.com', password='pass12345')
    client = APIClient()
    client.force_authenticate(user=user)

    payload = {
        'mode': 'one_time',
        'item_type': 'video',
        'item_id': 'fixture-video-1',
        'title': 'Integrity workout',
        'amount': '1500.00',
        'currency': 'RUB',
        'provider': 'mock',
        'idempotency_key': 'checkout-v845-fixture-1',
    }

    first = client.post('/api/v1/orders/checkout/', payload, format='json')
    second = client.post('/api/v1/orders/checkout/', payload, format='json')

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.data['order']['id'] == second.data['order']['id']
    assert first.data['payment']['id'] == second.data['payment']['id']
    assert Order.objects.count() == 1
    assert Payment.objects.count() == 1

    item = OrderItem.objects.get()
    integrity = item.metadata['checkout_integrity']
    assert integrity['schema_version'] == 'v8.45'
    assert integrity['idempotency_key'] == 'checkout-v845-fixture-1'
    assert integrity['price_snapshot']['requested_amount'] == '1500.00'
    assert integrity['price_snapshot']['resolved_amount'] == '1500.00'
    assert integrity['commission_snapshot']['gross_amount'] == '1500.00'
    assert integrity['commission_snapshot']['platform_commission']
    assert integrity['commission_snapshot']['trainer_net']


@pytest.mark.django_db
def test_checkout_integrity_reuses_pending_order_by_fingerprint_without_explicit_key():
    user = get_user_model().objects.create_user(email='buyer-fingerprint@example.com', password='pass12345')

    first = CheckoutIntegrityService.create_one_time_checkout(
        user=user,
        item_type='video',
        item_id='fixture-video-2',
        title='Fingerprint workout',
        amount=Decimal('990.00'),
        currency='RUB',
        provider='mock',
    )
    second = CheckoutIntegrityService.create_one_time_checkout(
        user=user,
        item_type='video',
        item_id='fixture-video-2',
        title='Fingerprint workout',
        amount=Decimal('990.00'),
        currency='RUB',
        provider='mock',
    )

    assert first.order.id == second.order.id
    assert second.reused_order is True
    assert second.reused_payment is True
    assert Order.objects.count() == 1
    assert Payment.objects.count() == 1
