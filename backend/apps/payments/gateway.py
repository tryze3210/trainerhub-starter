from __future__ import annotations

import os
from urllib.parse import urlencode, urlparse

from django.conf import settings

from apps.payments.models import PaymentProvider
from apps.platform_settings.selectors import get_payment_provider_settings

LOCAL_URL_HOSTS = {'localhost', '127.0.0.1', '0.0.0.0'}
API_PREFIXES = ('/api/v1', '/api')


def mock_payments_allowed() -> bool:
    return bool(getattr(settings, 'PAYMENTS_ALLOW_MOCK_PROVIDER', False))


def unverified_provider_return_allowed() -> bool:
    return bool(getattr(settings, 'PAYMENTS_ALLOW_UNVERIFIED_PROVIDER_RETURN', False))


class PaymentGatewayAdapter:
    def _normalize_public_base_url(self, value: str, *, setting_name: str, strip_api_prefix: bool = False) -> str:
        base_url = (value or '').strip().rstrip('/')
        if strip_api_prefix:
            for suffix in API_PREFIXES:
                if base_url.endswith(suffix):
                    base_url = base_url[: -len(suffix)].rstrip('/')
                    break

        parsed = urlparse(base_url)
        if bool(getattr(settings, 'IS_PRODUCTION', False)):
            host = (parsed.hostname or '').lower()
            if parsed.scheme != 'https' or not parsed.netloc or host in LOCAL_URL_HOSTS:
                raise ValueError(f'{setting_name} must be a public https:// URL in production.')
        return base_url

    def _frontend_base_url(self) -> str:
        base_url = (
            getattr(settings, 'FRONTEND_BASE_URL', '')
            or os.getenv('FRONTEND_BASE_URL')
            or os.getenv('NEXT_PUBLIC_APP_URL')
            or 'http://localhost:3000'
        )
        return self._normalize_public_base_url(base_url, setting_name='FRONTEND_BASE_URL')

    def _api_base_url(self) -> str:
        base_url = getattr(settings, 'API_BASE_URL', '') or os.getenv('API_BASE_URL') or 'http://localhost:8000'
        return self._normalize_public_base_url(base_url, setting_name='API_BASE_URL', strip_api_prefix=True)

    def _read_provider_settings(self) -> dict:
        return get_payment_provider_settings()

    def _provider_config(self, provider: str) -> dict:
        payload = self._read_provider_settings()
        for item in payload['providers']:
            if item.get('provider') == provider:
                return item
        return {'provider': provider, 'is_enabled': provider == PaymentProvider.MOCK}

    def _contract_urls(self, *, payment, provider: str, provider_config: dict | None = None) -> dict:
        frontend_base = self._frontend_base_url()
        api_base = self._api_base_url()
        return_qs = urlencode({'payment_id': str(payment.id)})
        provider_config = provider_config or {}
        return_url_override = (provider_config.get('return_url_override') or '').rstrip('/')
        frontend_return_url = return_url_override or f'{frontend_base}/checkout/success?payment_id={payment.id}&provider={provider}'
        frontend_cancel_url = f'{frontend_base}/checkout/cancel?payment_id={payment.id}&provider={provider}'
        return {
            'provider': provider,
            'frontend_return_url': frontend_return_url,
            'frontend_cancel_url': frontend_cancel_url,
            'provider_return_url_success': f'{api_base}/api/v1/payments/provider-return/?{return_qs}',
            'provider_return_url_cancel': f'{api_base}/api/v1/payments/provider-return/?{return_qs}',
            'provider_return_url_failed': f'{api_base}/api/v1/payments/provider-return/?{return_qs}',
            'webhook_url': f'{api_base}/api/v1/payments-webhooks/receive/',
        }

    def create_checkout(self, *, order, payment):
        provider = payment.provider or PaymentProvider.MOCK
        if provider == PaymentProvider.MOCK and not mock_payments_allowed():
            raise ValueError('Mock payment provider is disabled for this environment.')

        provider_config = self._provider_config(provider)
        if not provider_config.get('is_enabled', provider == PaymentProvider.MOCK):
            raise ValueError(f'Payment provider "{provider}" is disabled in platform settings.')

        contract = self._contract_urls(payment=payment, provider=provider, provider_config=provider_config)

        if provider == PaymentProvider.CLOUDPAYMENTS:
            public_id = provider_config.get('public_key') or os.getenv('CLOUDPAYMENTS_PUBLIC_ID', 'cloudpayments-public-id')
            return {
                'external_payment_id': f'cp-{payment.id}',
                'checkout_url': f'{contract["frontend_return_url"]}&mock=1&gateway=cloudpayments',
                'payload': {
                    **contract,
                    'adapter': 'cloudpayments',
                    'provider_config': provider_config,
                    'public_id': public_id,
                    'invoice_id': str(payment.id),
                    'description': f'Order {order.id}',
                },
            }

        if provider == PaymentProvider.YOOKASSA:
            shop_id = provider_config.get('shop_id') or os.getenv('YOOKASSA_SHOP_ID', 'yookassa-shop-id')
            return {
                'external_payment_id': f'yk-{payment.id}',
                'checkout_url': f'{contract["frontend_return_url"]}&mock=1&gateway=yookassa',
                'payload': {
                    **contract,
                    'adapter': 'yookassa',
                    'provider_config': provider_config,
                    'shop_id': shop_id,
                    'idempotence_key': f'payment-{payment.id}',
                    'description': f'Order {order.id}',
                },
            }

        return {
            'external_payment_id': f'mock-{payment.id}',
            'checkout_url': f'{contract["frontend_return_url"]}&mock=1&gateway=mock',
            'payload': {
                **contract,
                'adapter': 'mock',
                'provider_config': provider_config,
                'mock': True,
                'order_id': str(order.id),
            },
        }
