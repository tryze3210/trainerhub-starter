from rest_framework import serializers


class PaymentProviderConfigSerializer(serializers.Serializer):
    provider = serializers.CharField()
    display_name = serializers.CharField(required=False, allow_blank=True, default='')
    is_enabled = serializers.BooleanField(default=False)
    environment = serializers.CharField(required=False, allow_blank=True, default='test')
    public_key = serializers.CharField(required=False, allow_blank=True, default='')
    shop_id = serializers.CharField(required=False, allow_blank=True, default='')
    webhook_secret_masked = serializers.CharField(required=False, allow_blank=True, default='')
    return_url_override = serializers.CharField(required=False, allow_blank=True, default='')
    notes = serializers.CharField(required=False, allow_blank=True, default='')


class PaymentProviderSettingsSerializer(serializers.Serializer):
    default_provider = serializers.CharField(default='mock')
    providers = PaymentProviderConfigSerializer(many=True)


class PublicCheckoutPaymentProviderSerializer(serializers.Serializer):
    provider = serializers.CharField()
    display_name = serializers.CharField(required=False, allow_blank=True, default='')
    environment = serializers.CharField(required=False, allow_blank=True, default='')
    public_key = serializers.CharField(required=False, allow_blank=True, default='')


class PublicCheckoutPaymentSettingsSerializer(serializers.Serializer):
    default_provider = serializers.CharField(required=False, allow_blank=True, default='')
    providers = PublicCheckoutPaymentProviderSerializer(many=True)
