from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.customers.models import CustomerNote, CustomerSegment
from apps.orders.models import Order, OrderItem, OrderStatus, OrderType, PurchasedItemType


@pytest.mark.django_db
def test_v92_trainer_crm_lists_customer_notes_and_segments():
    User = get_user_model()
    trainer = User.objects.create_user(email='crm-trainer@example.com', password='pass12345', role='trainer')
    customer = User.objects.create_user(email='crm-customer@example.com', password='pass12345', role='customer')
    order = Order.objects.create(
        user=customer,
        order_type=OrderType.ONE_TIME,
        status=OrderStatus.PAID,
        currency='RUB',
        total_amount=Decimal('1200.00'),
    )
    OrderItem.objects.create(
        order=order,
        item_type=PurchasedItemType.VIDEO,
        item_id='crm-video-1',
        title_snapshot='CRM Video',
        quantity=1,
        unit_price=Decimal('1200.00'),
        total_price=Decimal('1200.00'),
        metadata={'trainer_id': str(trainer.id)},
    )

    client = APIClient()
    client.force_authenticate(user=trainer)

    response = client.get('/api/v1/customer/trainer-crm/')
    assert response.status_code == 200
    payload = response.json()
    assert payload['summary']['customers_count'] == 1
    assert payload['items'][0]['customer_id'] == str(customer.id)
    assert payload['items'][0]['total_spent'] == '1200.00'

    note_response = client.post(
        '/api/v1/customer/trainer-crm/notes/',
        {'customer_id': str(customer.id), 'body': 'Prefers morning sessions.', 'pinned': True},
        format='json',
    )
    assert note_response.status_code == 201
    assert CustomerNote.objects.filter(trainer=trainer, customer=customer, pinned=True).count() == 1

    segment_response = client.post(
        '/api/v1/customer/trainer-crm/segments/',
        {'name': 'High intent', 'description': 'Paid customers with active interest.'},
        format='json',
    )
    assert segment_response.status_code == 201
    segment = CustomerSegment.objects.get(trainer=trainer, name='High intent')

    assign_response = client.post(
        '/api/v1/customer/trainer-crm/segments/assign/',
        {'customer_id': str(customer.id), 'segment_id': str(segment.id)},
        format='json',
    )
    assert assign_response.status_code == 200

    detail_response = client.get(f'/api/v1/customer/trainer-crm/{customer.id}/')
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail['customer']['notes_count'] == 1
    assert detail['notes'][0]['body'] == 'Prefers morning sessions.'
    assert detail['segments'][0]['name'] == 'High intent'
