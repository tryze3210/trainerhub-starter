from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient

from apps.orders.services import OrderService
from apps.payments.models import Payment, PaymentProvider, PaymentStatus
from apps.payments.services import PaymentService


def _order(user):
    return OrderService.create_one_time_order(
        user=user,
        item_type='video',
        item_id='production-guard-video',
        title='Production guard video',
        amount=Decimal('990.00'),
    )


@pytest.mark.django_db
@override_settings(PAYMENTS_ALLOW_MOCK_PROVIDER=False)
def test_mock_checkout_provider_is_blocked_when_disabled():
    user = get_user_model().objects.create_user(email='mock-disabled@example.com', password='pass12345')
    order = _order(user)

    with pytest.raises(ValueError, match='Mock payment provider is disabled'):
        PaymentService.create_checkout_payment(order=order, provider=PaymentProvider.MOCK)

    assert Payment.objects.filter(order=order).count() == 0


@pytest.mark.django_db
def test_disabled_checkout_provider_does_not_leave_pending_payment():
    user = get_user_model().objects.create_user(email='provider-disabled@example.com', password='pass12345')
    order = _order(user)

    with pytest.raises(ValueError, match='disabled in platform settings'):
        PaymentService.create_checkout_payment(order=order, provider=PaymentProvider.CLOUDPAYMENTS)

    assert Payment.objects.filter(order=order).count() == 0


@pytest.mark.django_db
@override_settings(PAYMENTS_ALLOW_UNVERIFIED_PROVIDER_RETURN=False)
def test_unverified_provider_return_cannot_mutate_payment_status_when_disabled():
    user = get_user_model().objects.create_user(email='return-disabled@example.com', password='pass12345')
    order = _order(user)
    payment = Payment.objects.create(
        order=order,
        provider=PaymentProvider.MOCK,
        status=PaymentStatus.PENDING,
        amount=order.total_amount,
        currency=order.currency,
        external_payment_id='mock-return-disabled',
    )

    response = APIClient().get(f'/api/v1/payments/provider-return/?payment_id={payment.id}&status=succeeded')

    payment.refresh_from_db()
    assert response.status_code == 403
    assert payment.status == PaymentStatus.PENDING


@pytest.mark.django_db
@override_settings(PAYMENTS_ALLOW_MOCK_PROVIDER=False)
def test_mock_payment_actions_are_blocked_when_disabled():
    user = get_user_model().objects.create_user(email='mock-actions-disabled@example.com', password='pass12345')
    order = _order(user)
    payment = Payment.objects.create(
        order=order,
        provider=PaymentProvider.MOCK,
        status=PaymentStatus.PENDING,
        amount=order.total_amount,
        currency=order.currency,
        external_payment_id='mock-actions-disabled',
    )
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(f'/api/v1/payments/{payment.id}/confirm-mock/')

    payment.refresh_from_db()
    assert response.status_code == 403
    assert payment.status == PaymentStatus.PENDING
