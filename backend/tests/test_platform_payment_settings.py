import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from apps.platform_settings.models import PlatformSettings


@pytest.mark.django_db
def test_public_checkout_payment_settings_requires_no_auth_and_hides_disabled_providers():
    PlatformSettings.objects.create(
        homepage_config={
            'payments': {
                'default_provider': 'cloudpayments',
                'providers': [
                    {
                        'provider': 'mock',
                        'display_name': 'Тестовая оплата',
                        'is_enabled': True,
                        'environment': 'dev',
                        'public_key': 'mock-public',
                        'shop_id': 'mock-shop',
                        'webhook_secret_masked': 'secret',
                    },
                    {
                        'provider': 'cloudpayments',
                        'display_name': 'CloudPayments',
                        'is_enabled': True,
                        'environment': 'production',
                        'public_key': 'cp-public',
                        'shop_id': 'cp-shop',
                        'webhook_secret_masked': 'secret',
                    },
                    {
                        'provider': 'yookassa',
                        'display_name': 'ЮKassa',
                        'is_enabled': False,
                    },
                ],
            },
        },
    )

    response = APIClient().get('/api/v1/platform-settings/checkout-payment-providers/')

    assert response.status_code == 200
    assert response.data['default_provider'] == 'cloudpayments'
    assert response.data['providers'] == [
        {
            'provider': 'mock',
            'display_name': 'Тестовая оплата',
            'environment': 'dev',
            'public_key': 'mock-public',
        },
        {
            'provider': 'cloudpayments',
            'display_name': 'CloudPayments',
            'environment': 'production',
            'public_key': 'cp-public',
        },
    ]
    assert 'shop_id' not in response.data['providers'][0]
    assert 'webhook_secret_masked' not in response.data['providers'][0]


@pytest.mark.django_db
@override_settings(PAYMENTS_ALLOW_MOCK_PROVIDER=False)
def test_public_checkout_payment_settings_hides_mock_when_environment_disallows_it():
    PlatformSettings.objects.create(
        homepage_config={
            'payments': {
                'default_provider': 'mock',
                'providers': [
                    {'provider': 'mock', 'display_name': 'Тестовая оплата', 'is_enabled': True},
                    {'provider': 'cloudpayments', 'display_name': 'CloudPayments', 'is_enabled': True},
                ],
            },
        },
    )

    response = APIClient().get('/api/v1/platform-settings/checkout-payment-providers/')

    assert response.status_code == 200
    assert response.data['default_provider'] == 'cloudpayments'
    assert [item['provider'] for item in response.data['providers']] == ['cloudpayments']
