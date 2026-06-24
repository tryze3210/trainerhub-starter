from decimal import Decimal
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.entitlements.models import Entitlement, EntitlementSourceType, EntitlementStatus, EntitlementTargetType
from apps.orders.models import OrderStatus, PurchasedItemType
from apps.orders.services import OrderService
from apps.payments.models import PaymentProvider, PaymentStatus, PaymentWebhookEvent
from apps.payments.services import PaymentService


@pytest.mark.django_db
def test_payment_reconciliation_is_admin_only():
    user = get_user_model().objects.create_user(email='pay-recon-user@example.com', password='pass12345')
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get('/api/v1/ops/admin/payment-reconciliation/')

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_read_payment_reconciliation_mismatches():
    admin = get_user_model().objects.create_superuser(email='pay-recon-admin@example.com', password='pass12345')
    buyer = get_user_model().objects.create_user(email='pay-recon-buyer@example.com', password='pass12345')

    stale_order = OrderService.create_one_time_order(
        user=buyer,
        item_type=PurchasedItemType.VIDEO,
        item_id=uuid4(),
        title='Provider success stale order',
        amount=Decimal('1000.00'),
    )
    stale_payment = PaymentService.create_checkout_payment(order=stale_order, provider=PaymentProvider.MOCK)
    PaymentWebhookEvent.objects.create(
        provider=PaymentProvider.MOCK,
        event_type='payment.succeeded',
        external_event_id='evt_v85_provider_success_001',
        payment=stale_payment,
        status=PaymentWebhookEvent.Status.PROCESSED,
        payload={'external_payment_id': stale_payment.external_payment_id},
        processed_at=timezone.now(),
    )

    success_order = OrderService.create_one_time_order(
        user=buyer,
        item_type=PurchasedItemType.VIDEO,
        item_id=uuid4(),
        title='Internal success without access',
        amount=Decimal('500.00'),
    )
    success_payment = PaymentService.create_checkout_payment(order=success_order, provider=PaymentProvider.MOCK)
    success_payment.status = PaymentStatus.SUCCEEDED
    success_payment.confirmed_at = timezone.now()
    success_payment.save(update_fields=['status', 'confirmed_at', 'updated_at'])
    success_order.status = OrderStatus.COMPLETED
    success_order.save(update_fields=['status', 'updated_at'])

    refunded_order = OrderService.create_one_time_order(
        user=buyer,
        item_type=PurchasedItemType.VIDEO,
        item_id=uuid4(),
        title='Refunded with active access',
        amount=Decimal('300.00'),
    )
    refunded_payment = PaymentService.create_checkout_payment(order=refunded_order, provider=PaymentProvider.MOCK)
    refunded_payment.status = PaymentStatus.REFUNDED
    refunded_payment.provider_payload = {'refund_status': 'refunded'}
    refunded_payment.save(update_fields=['status', 'provider_payload', 'updated_at'])
    refunded_order.status = OrderStatus.REFUNDED
    refunded_order.save(update_fields=['status', 'updated_at'])
    Entitlement.objects.create(
        user=buyer,
        source_type=EntitlementSourceType.ORDER,
        source_order=refunded_order,
        target_type=EntitlementTargetType.VIDEO,
        target_id='refunded-active-v85',
        status=EntitlementStatus.ACTIVE,
    )

    client = APIClient()
    client.force_authenticate(user=admin)
    response = client.get('/api/v1/ops/admin/payment-reconciliation/?limit=20')

    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'critical'
    assert payload['metrics']['provider_payments']['successful_webhook_count'] == 1
    assert payload['metrics']['internal_payments']['succeeded_count'] == 1
    codes = {issue['code'] for issue in payload['issues']}
    assert 'provider_success_internal_not_succeeded' in codes
    assert 'internal_success_without_entitlement' in codes
    assert 'internal_refund_has_active_entitlement' in codes
