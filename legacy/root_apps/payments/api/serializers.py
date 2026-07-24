from rest_framework import serializers

from apps.payments.models import Payment, PaymentWebhookEvent


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
    headers = serializers.JSONField(required=False)
    signature = serializers.CharField(required=False, allow_blank=True)
    raw_payload_hash = serializers.CharField(required=False, allow_blank=True)


class PaymentWebhookEventSerializer(serializers.ModelSerializer):
    payment_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = PaymentWebhookEvent
        fields = [
            'id',
            'provider',
            'event_type',
            'external_event_id',
            'payment_id',
            'status',
            'payload',
            'headers',
            'signature',
            'raw_payload_hash',
            'error_message',
            'attempts',
            'received_at',
            'processed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
