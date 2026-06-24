from __future__ import annotations

import hashlib
import hmac
import json
from decimal import Decimal
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent
from apps.events.models import DomainEvent
from apps.orders.models import OrderStatus, PurchasedItemType
from apps.orders.services import OrderService
from apps.payments.models import PaymentProvider, PaymentStatus, PaymentWebhookEvent
from apps.payments.services import PaymentService, PaymentWebhookService
from apps.payments.webhook_security import PaymentWebhookSecurity, PaymentWebhookSignatureError


@pytest.mark.django_db
def test_payment_webhook_is_persisted_and_idempotent():
    user = get_user_model().objects.create_user(email='webhook-buyer@example.com', password='pass12345')
    order = OrderService.create_one_time_order(
        user=user,
        item_type=PurchasedItemType.VIDEO,
        item_id=uuid4(),
        title='Webhook paid video',
        amount=Decimal('499.00'),
    )
    payment = PaymentService.create_checkout_payment(order=order, provider=PaymentProvider.MOCK)

    event = PaymentWebhookService.handle(
        provider=PaymentProvider.MOCK,
        event_type='payment.succeeded',
        external_event_id='evt_webhook_001',
        payload={'external_payment_id': payment.external_payment_id, 'amount': '499.00'},
    )
    duplicate = PaymentWebhookService.handle(
        provider=PaymentProvider.MOCK,
        event_type='payment.succeeded',
        external_event_id='evt_webhook_001',
        payload={'external_payment_id': payment.external_payment_id, 'amount': '499.00'},
    )

    assert duplicate.id == event.id
    event.refresh_from_db()
    payment.refresh_from_db()
    order.refresh_from_db()

    assert event.status == PaymentWebhookEvent.Status.PROCESSED
    assert event.attempts == 1
    assert event.payment_id == payment.id
    assert event.processed_at is not None
    assert payment.status == PaymentStatus.SUCCEEDED
    assert order.status == OrderStatus.COMPLETED
    assert DomainEvent.objects.filter(event_type='payment.webhook_processed').count() == 1
    assert DomainEvent.objects.filter(event_type='payment.webhook_duplicate').count() == 1
    assert AuditEvent.objects.filter(event_type='payment.webhook_processed', entity_id=str(event.id)).exists()
    assert AuditEvent.objects.filter(event_type='payment.webhook_duplicate', entity_id=str(event.id)).exists()


@pytest.mark.django_db
def test_payment_webhook_raw_signature_verification(monkeypatch):
    monkeypatch.setenv('CLOUDPAYMENTS_WEBHOOK_SECRET', 'super-secret-webhook-key')
    payload = {
        'provider': PaymentProvider.CLOUDPAYMENTS,
        'event_type': 'payment.succeeded',
        'external_event_id': 'evt_signed_001',
        'external_payment_id': 'cp-payment-001',
    }
    raw_body = json.dumps(payload, separators=(',', ':'), sort_keys=True).encode('utf-8')
    signature = hmac.new(b'super-secret-webhook-key', raw_body, hashlib.sha256).hexdigest()

    normalized = PaymentWebhookSecurity.normalize(
        provider=PaymentProvider.CLOUDPAYMENTS,
        payload=payload,
        raw_body=raw_body,
        headers={'X-Provider-Signature': signature},
        verify_signature=True,
    )

    assert normalized.provider == PaymentProvider.CLOUDPAYMENTS
    assert normalized.event_type == 'payment.succeeded'
    assert normalized.external_event_id == 'evt_signed_001'
    assert normalized.raw_payload_hash == hashlib.sha256(raw_body).hexdigest()


@pytest.mark.django_db
def test_payment_webhook_replay_timestamp_can_be_required(monkeypatch):
    monkeypatch.setenv('CLOUDPAYMENTS_WEBHOOK_SECRET', 'super-secret-webhook-key')
    monkeypatch.setenv('CLOUDPAYMENTS_WEBHOOK_REQUIRE_TIMESTAMP', 'true')
    monkeypatch.setenv('CLOUDPAYMENTS_WEBHOOK_REPLAY_TOLERANCE_SECONDS', '60')
    payload = {
        'provider': PaymentProvider.CLOUDPAYMENTS,
        'event_type': 'payment.succeeded',
        'external_event_id': 'evt_signed_replay_001',
        'external_payment_id': 'cp-payment-replay-001',
    }
    raw_body = json.dumps(payload, separators=(',', ':'), sort_keys=True).encode('utf-8')
    signature = hmac.new(b'super-secret-webhook-key', raw_body, hashlib.sha256).hexdigest()
    old_timestamp = str(int((timezone.now() - timezone.timedelta(minutes=10)).timestamp()))

    with pytest.raises(PaymentWebhookSignatureError, match='replay tolerance'):
        PaymentWebhookSecurity.normalize(
            provider=PaymentProvider.CLOUDPAYMENTS,
            payload=payload,
            raw_body=raw_body,
            headers={'X-Provider-Signature': signature, 'X-Provider-Timestamp': old_timestamp},
            verify_signature=True,
        )


@pytest.mark.django_db
def test_payment_webhook_duplicate_raw_payload_hash_is_rejected_as_duplicate():
    user = get_user_model().objects.create_user(email='webhook-raw-duplicate@example.com', password='pass12345')
    order = OrderService.create_one_time_order(
        user=user,
        item_type=PurchasedItemType.VIDEO,
        item_id=uuid4(),
        title='Webhook raw duplicate video',
        amount=Decimal('499.00'),
    )
    payment = PaymentService.create_checkout_payment(order=order, provider=PaymentProvider.MOCK)
    raw_hash = 'same-raw-hash-v80'

    first = PaymentWebhookService.handle(
        provider=PaymentProvider.MOCK,
        event_type='payment.succeeded',
        external_event_id='evt_raw_hash_001',
        payload={'external_payment_id': payment.external_payment_id, 'amount': '499.00'},
        raw_payload_hash=raw_hash,
    )
    duplicate = PaymentWebhookService.handle(
        provider=PaymentProvider.MOCK,
        event_type='payment.succeeded',
        external_event_id='evt_raw_hash_002',
        payload={'external_payment_id': payment.external_payment_id, 'amount': '499.00'},
        raw_payload_hash=raw_hash,
    )

    assert first.status == PaymentWebhookEvent.Status.PROCESSED
    assert duplicate.id != first.id
    assert duplicate.status == PaymentWebhookEvent.Status.DUPLICATE
    assert duplicate.payment_id == payment.id
    assert 'raw payload hash' in duplicate.error_message
    assert AuditEvent.objects.filter(
        event_type='payment.webhook_duplicate',
        entity_id=str(duplicate.id),
        context__duplicate_reason='raw_payload_hash_already_seen',
    ).exists()


@pytest.mark.django_db
def test_rejected_payment_webhook_is_audited(monkeypatch):
    monkeypatch.setenv('CLOUDPAYMENTS_WEBHOOK_SECRET', 'super-secret-webhook-key')
    payload = {
        'provider': PaymentProvider.CLOUDPAYMENTS,
        'event_type': 'payment.succeeded',
        'external_event_id': 'evt_bad_signature_001',
        'external_payment_id': 'cp-payment-bad-signature-001',
    }

    response = APIClient().post(
        '/api/v1/payments-webhooks/receive/?provider=cloudpayments',
        payload,
        format='json',
        HTTP_X_PROVIDER_SIGNATURE='bad-signature',
    )

    assert response.status_code == 400
    event = AuditEvent.objects.get(event_type='payment.webhook_rejected')
    assert event.entity_type == 'payment_webhook'
    assert event.context['reason'] == 'Invalid payment webhook signature.'
    assert event.context['provider'] == 'cloudpayments'
