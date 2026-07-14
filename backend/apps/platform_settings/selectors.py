from __future__ import annotations

from copy import deepcopy

from django.conf import settings

from apps.platform_settings.models import PlatformSettings


DEFAULT_PAYMENT_SETTINGS = {
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


def get_platform_settings() -> PlatformSettings:
    settings_obj = PlatformSettings.objects.order_by('created_at').first()
    if settings_obj:
        return settings_obj
    return PlatformSettings.objects.create()


def get_payment_provider_settings() -> dict:
    settings_obj = get_platform_settings()
    payload = deepcopy(DEFAULT_PAYMENT_SETTINGS)
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


def get_public_checkout_payment_settings() -> dict:
    payload = get_payment_provider_settings()
    providers = []
    for provider in payload['providers']:
        code = provider.get('provider')
        if code == 'mock' and not getattr(settings, 'PAYMENTS_ALLOW_MOCK_PROVIDER', False):
            continue
        if not provider.get('is_enabled'):
            continue
        providers.append(
            {
                'provider': code,
                'display_name': provider.get('display_name') or code,
                'environment': provider.get('environment') or '',
                'public_key': provider.get('public_key') or '',
            }
        )

    default_provider = payload.get('default_provider') or ''
    if default_provider not in {item['provider'] for item in providers}:
        default_provider = providers[0]['provider'] if providers else ''

    return {
        'default_provider': default_provider,
        'providers': providers,
    }
