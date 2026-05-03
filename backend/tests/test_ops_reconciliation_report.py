from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.orders.models import Order, OrderStatus, OrderType


@pytest.mark.django_db
def test_reconciliation_report_is_admin_only():
    user = get_user_model().objects.create_user(email='recon-user@example.com', password='pass12345')
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get('/api/v1/ops/admin/reconciliation-report/')

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_read_reconciliation_report_and_see_order_access_gap():
    admin = get_user_model().objects.create_superuser(email='recon-admin@example.com', password='pass12345')
    buyer = get_user_model().objects.create_user(email='recon-buyer@example.com', password='pass12345')
    order = Order.objects.create(
        user=buyer,
        order_type=OrderType.ONE_TIME,
        status=OrderStatus.COMPLETED,
        currency='RUB',
        total_amount=Decimal('1000.00'),
    )

    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get('/api/v1/ops/admin/reconciliation-report/?limit=20')

    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] in {'ok', 'degraded', 'critical'}
    assert set(payload['sections'].keys()) == {'payments', 'orders', 'entitlements', 'payouts', 'webhooks', 'outbox'}
    order_issues = payload['sections']['orders']['issues']
    assert any(
        issue['code'] == 'completed_order_without_active_entitlement' and issue['entity_id'] == str(order.id)
        for issue in order_issues
    )
