from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.platform_settings.api.serializers import (
    PaymentProviderSettingsSerializer,
    PublicCheckoutPaymentSettingsSerializer,
)
from apps.platform_settings.selectors import (
    get_platform_settings,
    get_payment_provider_settings,
    get_public_checkout_payment_settings,
)


class PaymentProviderSettingsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def _read_payload(self):
        settings_obj = get_platform_settings()
        payload = get_payment_provider_settings()
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


class PublicCheckoutPaymentSettingsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        payload = get_public_checkout_payment_settings()
        serializer = PublicCheckoutPaymentSettingsSerializer(payload)
        return Response(serializer.data)
