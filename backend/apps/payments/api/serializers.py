from rest_framework import serializers
from apps.payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id',
            'order_id',
            'provider',
            'status',
            'amount',
            'currency',
            'external_payment_id',
            'external_checkout_url',
            'provider_payload',
            'confirmed_at',
            'created_at',
            'updated_at',
        ]


class PaymentWebhookSerializer(serializers.Serializer):
    provider = serializers.CharField()
    event_type = serializers.CharField()
    external_event_id = serializers.CharField()
    payload = serializers.JSONField()
