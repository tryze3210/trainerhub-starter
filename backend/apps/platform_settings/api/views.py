from copy import deepcopy

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.platform_settings.api.serializers import PaymentProviderSettingsSerializer
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


class PaymentProviderSettingsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def _read_payload(self):
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
        return settings_obj, payload

    def get(self, request, *args, **kwargs):
        _settings_obj, payload = self._read_payload()
        serializer = PaymentProviderSettingsSerializer(payload)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        settings_obj, _payload = self._read_payload()
        serializer = PaymentProviderSettingsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        homepage_config = settings_obj.homepage_config or {}
        homepage_config['payments'] = serializer.validated_data
        settings_obj.homepage_config = homepage_config
        settings_obj.save(update_fields=['homepage_config', 'updated_at'])
        return Response(PaymentProviderSettingsSerializer(serializer.validated_data).data)
