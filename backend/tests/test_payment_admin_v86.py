from decimal import Decimal
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.entitlements.models import Entitlement, EntitlementSourceType, EntitlementStatus, EntitlementTargetType
from apps.orders.models import PurchasedItemType
from apps.orders.services import OrderService
from apps.payments.models import PaymentProvider, PaymentStatus
from apps.payments.services import PaymentService


@pytest.mark.django_db
def test_payment_admin_list_is_admin_only():
    user = get_user_model().objects.create_user(email='payment-admin-user@example.com', password='pass12345')
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get('/api/v1/payments-admin/')

    assert response.status_code == 403


@pytest.mark.django_db
def test_payment_admin_list_includes_refunds_and_entitlement_status():
    admin = get_user_model().objects.create_superuser(email='payment-admin@example.com', password='pass12345')
    buyer = get_user_model().objects.create_user(email='payment-admin-buyer@example.com', password='pass12345')
    order = OrderService.create_one_time_order(
        user=buyer,
        item_type=PurchasedItemType.VIDEO,
        item_id=uuid4(),
        title='Payment admin access',
        amount=Decimal('1200.00'),
    )
    payment = PaymentService.create_checkout_payment(order=order, provider=PaymentProvider.MOCK)
    payment.status = PaymentStatus.REFUNDED
    payment.provider_payload = {
        'refund_operations': [
            {
                'refund_id': 'refund-v86-001',
                'amount': '400.00',
                'status': 'succeeded',
                'reason': 'customer_request',
            }
        ]
    }
    payment.save(update_fields=['status', 'provider_payload', 'updated_at'])
    Entitlement.objects.create(
        user=buyer,
        source_type=EntitlementSourceType.ORDER,
        source_order=order,
        target_type=EntitlementTargetType.VIDEO,
        target_id='payment-admin-video',
        status=EntitlementStatus.REVOKED,
    )

    client = APIClient()
    client.force_authenticate(user=admin)
    response = client.get('/api/v1/payments-admin/', {'buyer_email': 'payment-admin-buyer', 'limit': 10})

    assert response.status_code == 200
    payload = response.json()
    rows = payload['results'] if isinstance(payload, dict) and 'results' in payload else payload
    assert rows[0]['id'] == str(payment.id)
    assert rows[0]['buyer_email'] == 'payment-admin-buyer@example.com'
    assert rows[0]['order_status'] == order.status
    assert rows[0]['refund_operations'][0]['refund_id'] == 'refund-v86-001'
    assert rows[0]['entitlement_summary']['status'] == 'revoked'
    assert rows[0]['entitlement_summary']['revoked'] == 1
