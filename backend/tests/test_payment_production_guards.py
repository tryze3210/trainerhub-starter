import hashlib
import hmac
import json
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient

from apps.orders.services import OrderService
from apps.payments.gateway import PaymentGatewayAdapter
from apps.payments.models import Payment, PaymentProvider, PaymentStatus, PaymentWebhookEvent
from apps.payments.services import PaymentService, PaymentWebhookService


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
@override_settings(
    IS_PRODUCTION=True,
    API_BASE_URL='http://localhost:8000',
    FRONTEND_BASE_URL='https://trainerhub.example.com',
)
def test_gateway_blocks_local_api_base_url_in_production():
    with pytest.raises(ValueError, match='API_BASE_URL'):
        PaymentGatewayAdapter()._api_base_url()


@pytest.mark.django_db
@override_settings(
    IS_PRODUCTION=True,
    API_BASE_URL='https://api.trainerhub.example.com/api/v1',
    FRONTEND_BASE_URL='http://localhost:8080',
)
def test_gateway_blocks_local_frontend_base_url_in_production():
    adapter = PaymentGatewayAdapter()

    assert adapter._api_base_url() == 'https://api.trainerhub.example.com'
    with pytest.raises(ValueError, match='FRONTEND_BASE_URL'):
        adapter._frontend_base_url()


@pytest.mark.django_db
@override_settings(PAYMENTS_ALLOW_UNVERIFIED_PROVIDER_RETURN=False)
def test_provider_return_cannot_mutate_payment_status_from_query_params():
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
    assert response.status_code == 200
    assert payment.status == PaymentStatus.PENDING
    assert response.data['redirect_path'] == f'/payments/{payment.id}'


@pytest.mark.django_db
@override_settings(PAYMENTS_ALLOW_UNVERIFIED_PROVIDER_RETURN=True)
def test_provider_return_ignores_legacy_unverified_return_flag():
    user = get_user_model().objects.create_user(email='return-enabled@example.com', password='pass12345')
    order = _order(user)
    payment = Payment.objects.create(
        order=order,
        provider=PaymentProvider.MOCK,
        status=PaymentStatus.PENDING,
        amount=order.total_amount,
        currency=order.currency,
        external_payment_id='mock-return-enabled',
    )

    response = APIClient().get(f'/api/v1/payments/provider-return/?payment_id={payment.id}&status=succeeded')

    payment.refresh_from_db()
    assert response.status_code == 200
    assert payment.status == PaymentStatus.PENDING
    assert response.data['payment_status'] == PaymentStatus.PENDING


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


@pytest.mark.django_db
@override_settings(PAYMENTS_WEBHOOK_SECRET='webhook-secret')
def test_public_webhook_receive_rejects_unsigned_canonical_payload():
    response = APIClient().post(
        '/api/v1/payments-webhooks/receive/',
        {
            'provider': 'mock',
            'event_type': 'payment.succeeded',
            'external_event_id': 'unsigned-canonical-event',
            'payload': {
                'external_payment_id': 'mock-payment-id',
            },
        },
        format='json',
        HTTP_X_PAYMENT_PROVIDER='mock',
    )

    assert response.status_code == 400
    assert response.data['detail'] == 'Invalid payment webhook signature.'
    assert not PaymentWebhookEvent.objects.filter(external_event_id='unsigned-canonical-event').exists()


@pytest.mark.django_db
@override_settings(PAYMENTS_WEBHOOK_SECRET='webhook-secret', PAYMENTS_WEBHOOK_REQUIRE_TIMESTAMP=True)
def test_public_webhook_receive_requires_timestamp_when_enabled():
    payload = {
        'provider': 'mock',
        'event_type': 'payment.succeeded',
        'external_event_id': 'missing-timestamp-event',
        'external_payment_id': 'mock-payment-id',
    }
    raw_body = json.dumps(payload, separators=(',', ':'), sort_keys=True).encode('utf-8')
    signature = hmac.new(b'webhook-secret', raw_body, hashlib.sha256).hexdigest()

    response = APIClient().generic(
        'POST',
        '/api/v1/payments-webhooks/receive/',
        raw_body,
        content_type='application/json',
        HTTP_X_PAYMENT_PROVIDER='mock',
        HTTP_X_PROVIDER_SIGNATURE=signature,
    )

    assert response.status_code == 400
    assert response.data['detail'] == 'Payment webhook timestamp is required.'
    assert not PaymentWebhookEvent.objects.filter(external_event_id='missing-timestamp-event').exists()


@pytest.mark.django_db
@override_settings(PAYMENTS_WEBHOOK_MAX_BODY_BYTES=64)
def test_public_webhook_receive_rejects_oversized_payload_before_ingestion():
    raw_body = json.dumps(
        {
            'provider': 'mock',
            'event_type': 'payment.succeeded',
            'external_event_id': 'oversized-webhook-event',
            'external_payment_id': 'mock-payment-id',
            'extra': 'x' * 256,
        },
        separators=(',', ':'),
        sort_keys=True,
    ).encode('utf-8')

    response = APIClient().generic(
        'POST',
        '/api/v1/payments-webhooks/receive/',
        raw_body,
        content_type='application/json',
        HTTP_X_PAYMENT_PROVIDER='mock',
    )

    assert response.status_code == 400
    assert response.data['detail'] == 'Payment webhook payload exceeds maximum size.'
    assert not PaymentWebhookEvent.objects.filter(external_event_id='oversized-webhook-event').exists()


@pytest.mark.django_db
def test_webhook_idempotency_is_scoped_by_provider_event_id():
    first_user = get_user_model().objects.create_user(email='provider-event-1@example.com', password='pass12345')
    second_user = get_user_model().objects.create_user(email='provider-event-2@example.com', password='pass12345')
    first_order = _order(first_user)
    second_order = _order(second_user)
    first_order.items.update(item_type='provider_event_test')
    second_order.items.update(item_type='provider_event_test')
    first_payment = Payment.objects.create(
        order=first_order,
        provider=PaymentProvider.MOCK,
        status=PaymentStatus.PENDING,
        amount=first_order.total_amount,
        currency=first_order.currency,
        external_payment_id='provider-event-payment-1',
    )
    second_payment = Payment.objects.create(
        order=second_order,
        provider=PaymentProvider.YOOKASSA,
        status=PaymentStatus.PENDING,
        amount=second_order.total_amount,
        currency=second_order.currency,
        external_payment_id='provider-event-payment-2',
    )

    first_event = PaymentWebhookService.handle(
        provider=PaymentProvider.MOCK,
        event_type='payment.succeeded',
        external_event_id='shared-provider-event-id',
        payload={'external_payment_id': first_payment.external_payment_id},
    )
    second_event = PaymentWebhookService.handle(
        provider=PaymentProvider.YOOKASSA,
        event_type='payment.succeeded',
        external_event_id='shared-provider-event-id',
        payload={'external_payment_id': second_payment.external_payment_id},
    )
    duplicate = PaymentWebhookService.handle(
        provider=PaymentProvider.MOCK,
        event_type='payment.succeeded',
        external_event_id='shared-provider-event-id',
        payload={'external_payment_id': first_payment.external_payment_id},
    )

    assert first_event.id != second_event.id
    assert duplicate.id == first_event.id
    assert first_event.provider_event_id == 'mock:shared-provider-event-id'
    assert second_event.provider_event_id == 'yookassa:shared-provider-event-id'
    assert PaymentWebhookEvent.objects.filter(external_event_id='shared-provider-event-id').count() == 2
