from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from datetime import timezone as datetime_timezone
from typing import Any, Mapping

from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.payments.models import PaymentProvider


SIGNATURE_HEADERS = (
    'X-Provider-Signature',
    'X-Signature',
    'X-Webhook-Signature',
    'X-Yookassa-Signature',
    'X-Cloudpayments-Signature',
)

TIMESTAMP_HEADERS = (
    'X-Provider-Timestamp',
    'X-Webhook-Timestamp',
    'X-Request-Timestamp',
    'X-Yookassa-Timestamp',
    'X-Cloudpayments-Timestamp',
)


@dataclass(frozen=True)
class NormalizedWebhookPayload:
    provider: str
    event_type: str
    external_event_id: str
    external_payment_id: str
    payload: dict[str, Any]
    headers: dict[str, str]
    signature: str
    raw_payload_hash: str


class PaymentWebhookSignatureError(ValueError):
    pass


class PaymentWebhookPayloadError(ValueError):
    pass


class PaymentWebhookSecurity:
    """Provider-neutral webhook parsing and signature verification.

    The adapters are intentionally conservative: raw body verification is used
    whenever a secret is configured; unsigned local mock webhooks are allowed so
    developer smoke tests and current contract tests keep working.
    """

    @staticmethod
    def raw_hash(raw_body: bytes) -> str:
        return hashlib.sha256(raw_body or b'').hexdigest()

    @staticmethod
    def json_bytes(payload: Mapping[str, Any]) -> bytes:
        return json.dumps(payload, separators=(',', ':'), sort_keys=True).encode('utf-8')

    @staticmethod
    def signature_from_headers(headers: Mapping[str, Any]) -> str:
        for name in SIGNATURE_HEADERS:
            value = headers.get(name) or headers.get(name.lower())
            if value:
                return str(value).strip()
        return ''

    @staticmethod
    def provider_secret(provider: str) -> str:
        normalized = (provider or PaymentProvider.MOCK).upper().replace('-', '_')
        candidates = [
            f'{normalized}_WEBHOOK_SECRET',
            f'PAYMENTS_{normalized}_WEBHOOK_SECRET',
            'PAYMENTS_WEBHOOK_SECRET',
        ]
        for name in candidates:
            value = os.getenv(name) or getattr(settings, name, '')
            if value:
                return str(value)
        return ''

    @staticmethod
    def require_timestamp(provider: str) -> bool:
        normalized = (provider or PaymentProvider.MOCK).upper().replace('-', '_')
        candidates = [
            f'{normalized}_WEBHOOK_REQUIRE_TIMESTAMP',
            f'PAYMENTS_{normalized}_WEBHOOK_REQUIRE_TIMESTAMP',
            'PAYMENTS_WEBHOOK_REQUIRE_TIMESTAMP',
        ]
        for name in candidates:
            value = os.getenv(name)
            if value is None:
                value = getattr(settings, name, None)
            if value is not None:
                return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}
        return False

    @staticmethod
    def replay_tolerance_seconds(provider: str) -> int:
        normalized = (provider or PaymentProvider.MOCK).upper().replace('-', '_')
        candidates = [
            f'{normalized}_WEBHOOK_REPLAY_TOLERANCE_SECONDS',
            f'PAYMENTS_{normalized}_WEBHOOK_REPLAY_TOLERANCE_SECONDS',
            'PAYMENTS_WEBHOOK_REPLAY_TOLERANCE_SECONDS',
        ]
        for name in candidates:
            value = os.getenv(name) or getattr(settings, name, None)
            if value:
                try:
                    return max(1, int(value))
                except (TypeError, ValueError):
                    return 300
        return 300

    @staticmethod
    def _digest(raw_body: bytes, secret: str) -> str:
        return hmac.new(secret.encode('utf-8'), raw_body, hashlib.sha256).hexdigest()

    @staticmethod
    def timestamp_from_headers(headers: Mapping[str, Any]) -> str:
        for name in TIMESTAMP_HEADERS:
            value = headers.get(name) or headers.get(name.lower())
            if value:
                return str(value).strip()
        return ''

    @classmethod
    def validate_replay_window(cls, *, provider: str, headers: Mapping[str, Any]) -> None:
        timestamp = cls.timestamp_from_headers(headers)
        if not timestamp:
            if cls.require_timestamp(provider):
                raise PaymentWebhookSignatureError('Payment webhook timestamp is required.')
            return

        parsed = None
        if timestamp.isdigit():
            parsed = timezone.datetime.fromtimestamp(int(timestamp), tz=datetime_timezone.utc)
        else:
            parsed = parse_datetime(timestamp)
            if parsed and timezone.is_naive(parsed):
                parsed = timezone.make_aware(parsed, datetime_timezone.utc)
        if not parsed:
            raise PaymentWebhookSignatureError('Invalid payment webhook timestamp.')

        age = abs((timezone.now() - parsed).total_seconds())
        if age > cls.replay_tolerance_seconds(provider):
            raise PaymentWebhookSignatureError('Payment webhook timestamp is outside replay tolerance.')

    @classmethod
    def verify_signature(cls, *, provider: str, raw_body: bytes, signature: str) -> bool:
        secret = cls.provider_secret(provider)
        if not secret:
            # Local mock provider remains unsigned. Real providers must set a
            # secret in environment/platform config before production rollout.
            return provider == PaymentProvider.MOCK
        if not signature:
            return False

        expected_hex = cls._digest(raw_body, secret)
        supplied = signature.strip()
        allowed = {
            expected_hex,
            f'sha256={expected_hex}',
        }
        expected_b64 = base64.b64encode(bytes.fromhex(expected_hex)).decode('ascii')
        allowed.add(expected_b64)
        return any(hmac.compare_digest(supplied, item) for item in allowed)

    @staticmethod
    def _first_value(payload: Mapping[str, Any], keys: tuple[str, ...]) -> str:
        for key in keys:
            value = payload.get(key)
            if value not in (None, ''):
                return str(value)
        return ''

    @classmethod
    def normalize(
        cls,
        *,
        provider: str | None,
        payload: Mapping[str, Any],
        headers: Mapping[str, Any] | None = None,
        raw_body: bytes | None = None,
        signature: str | None = None,
        verify_signature: bool = True,
    ) -> NormalizedWebhookPayload:
        payload_dict = dict(payload or {})
        provider_value = (provider or payload_dict.get('provider') or PaymentProvider.MOCK).strip().lower()
        headers_dict = {str(k): str(v) for k, v in dict(headers or {}).items()}
        body = raw_body if raw_body is not None else cls.json_bytes(payload_dict)
        signature_value = signature if signature is not None else cls.signature_from_headers(headers_dict)

        if verify_signature:
            cls.validate_replay_window(provider=provider_value, headers=headers_dict)

        if verify_signature and not cls.verify_signature(provider=provider_value, raw_body=body, signature=signature_value or ''):
            raise PaymentWebhookSignatureError('Invalid payment webhook signature.')

        nested_object = payload_dict.get('object') if isinstance(payload_dict.get('object'), dict) else {}
        nested_data = payload_dict.get('data') if isinstance(payload_dict.get('data'), dict) else {}
        nested_payment = nested_data.get('payment') if isinstance(nested_data.get('payment'), dict) else {}
        flat_payload = {**nested_object, **nested_payment, **payload_dict}

        event_type = cls._first_value(flat_payload, ('event_type', 'type', 'event', 'notification_type'))
        external_payment_id = cls._first_value(
            flat_payload,
            ('external_payment_id', 'provider_payment_id', 'payment_id', 'providerPaymentId', 'invoice_id', 'InvoiceId', 'id'),
        )
        external_event_id = cls._first_value(
            flat_payload,
            ('external_event_id', 'event_id', 'eventId', 'notification_id', 'idempotence_key', 'id'),
        )

        if not event_type:
            raise PaymentWebhookPayloadError('Webhook payload must include event_type/type/event.')
        if not external_payment_id:
            raise PaymentWebhookPayloadError('Webhook payload must include external_payment_id/payment_id.')
        if not external_event_id:
            payload_hash = cls.raw_hash(body)
            external_event_id = f'{provider_value}:{event_type}:{external_payment_id}:{payload_hash[:24]}'

        normalized_payload = {
            **payload_dict,
            'provider': provider_value,
            'event_type': event_type,
            'external_payment_id': external_payment_id,
            'external_event_id': external_event_id,
        }

        return NormalizedWebhookPayload(
            provider=provider_value,
            event_type=event_type,
            external_event_id=external_event_id,
            external_payment_id=external_payment_id,
            payload=normalized_payload,
            headers=headers_dict,
            signature=signature_value or '',
            raw_payload_hash=cls.raw_hash(body),
        )
