from __future__ import annotations

import os
from copy import deepcopy
from urllib.parse import urlencode

from django.conf import settings

from apps.payments.models import PaymentProvider
from apps.platform_settings.models import PlatformSettings


DEFAULT_PROVIDER_SETTINGS = {
    'default_provider': 'mock',
    'providers': [
        {
            'provider': 'mock',
            'display_name': 'Mock checkout',
            'is_enabled': True,
            'environment': 'dev',
            'public_key': '',
            'shop_id': '',
            'webhook_secret_masked': '',
            'return_url_override': '',
            'notes': 'Always available for local development.',
        },
        {
            'provider': 'cloudpayments',
            'display_name': 'CloudPayments',
            'is_enabled': False,
            'environment': 'test',
            'public_key': '',
            'shop_id': '',
            'webhook_secret_masked': '',
            'return_url_override': '',
            'notes': '',
        },
        {
            'provider': 'yookassa',
            'display_name': 'YooKassa',
            'is_enabled': False,
            'environment': 'test',
            'public_key': '',
            'shop_id': '',
            'webhook_secret_masked': '',
            'return_url_override': '',
            'notes': '',
        },
    ],
}


class PaymentGatewayAdapter:
    def _frontend_base_url(self) -> str:
        return (
            os.getenv('FRONTEND_BASE_URL')
            or os.getenv('NEXT_PUBLIC_APP_URL')
            or 'http://localhost:3000'
        ).rstrip('/')

    def _api_base_url(self) -> str:
        candidates = getattr(settings, 'ALLOWED_HOSTS', [])
        if '127.0.0.1' in candidates:
            host = '127.0.0.1'
        else:
            host = 'localhost'
        return f'http://{host}:8000'

    def _read_provider_settings(self) -> dict:
        payload = deepcopy(DEFAULT_PROVIDER_SETTINGS)
        settings_obj = PlatformSettings.objects.order_by('created_at').first()
        if not settings_obj:
            return payload
        stored = ((settings_obj.homepage_config or {}).get('payments') or {})
        if stored.get('default_provider'):
            payload['default_provider'] = stored['default_provider']
        provider_map = {item['provider']: item for item in payload['providers']}
        for item in stored.get('providers', []):
            provider = item.get('provider')
            if not provider:
                continue
            if provider not in provider_map:
                provider_map[provider] = {'provider': provider}
            provider_map[provider].update(item)
        payload['providers'] = list(provider_map.values())
        return payload

    def _provider_config(self, provider: str) -> dict:
        payload = self._read_provider_settings()
        for item in payload['providers']:
            if item.get('provider') == provider:
                return item
        return {'provider': provider, 'is_enabled': provider == PaymentProvider.MOCK}

    def _contract_urls(self, *, payment, provider: str, provider_config: dict | None = None) -> dict:
        frontend_base = self._frontend_base_url()
        api_base = self._api_base_url()
        success_qs = urlencode({'payment_id': str(payment.id), 'status': 'succeeded'})
        cancel_qs = urlencode({'payment_id': str(payment.id), 'status': 'cancelled'})
        failed_qs = urlencode({'payment_id': str(payment.id), 'status': 'failed'})
        provider_config = provider_config or {}
        return_url_override = (provider_config.get('return_url_override') or '').rstrip('/')
        frontend_return_url = return_url_override or f'{frontend_base}/checkout/success?payment_id={payment.id}&provider={provider}'
        frontend_cancel_url = f'{frontend_base}/checkout/cancel?payment_id={payment.id}&provider={provider}'
        return {
            'provider': provider,
            'frontend_return_url': frontend_return_url,
            'frontend_cancel_url': frontend_cancel_url,
            'provider_return_url_success': f'{api_base}/api/v1/payments/provider-return/?{success_qs}',
            'provider_return_url_cancel': f'{api_base}/api/v1/payments/provider-return/?{cancel_qs}',
            'provider_return_url_failed': f'{api_base}/api/v1/payments/provider-return/?{failed_qs}',
            'webhook_url': f'{api_base}/api/v1/payments-webhooks/receive/',
        }

    def create_checkout(self, *, order, payment):
        provider = payment.provider or PaymentProvider.MOCK
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
