from rest_framework import serializers


class ModerationQueueItemSerializer(serializers.Serializer):
    id = serializers.CharField()
    entity_type = serializers.CharField()
    entity_id = serializers.CharField()
    status = serializers.CharField()
    reason = serializers.CharField(allow_blank=True)
    submitted_at = serializers.DateTimeField()


class PaymentAdminSerializer(serializers.Serializer):
    id = serializers.CharField()
    payer_id = serializers.CharField()
    order_id = serializers.CharField()
    provider = serializers.CharField()
    provider_payment_id = serializers.CharField(allow_blank=True)
    status = serializers.CharField()
    gross_amount = serializers.CharField()
    platform_fee = serializers.CharField()
    trainer_amount = serializers.CharField()
    created_at = serializers.DateTimeField()
    paid_at = serializers.DateTimeField(allow_null=True)


class PayoutAdminSerializer(serializers.Serializer):
    id = serializers.CharField()
    trainer_id = serializers.CharField()
    amount = serializers.CharField()
    currency = serializers.CharField()
    status = serializers.CharField()
    destination_masked = serializers.CharField(allow_blank=True)
    requested_at = serializers.DateTimeField()
    approved_at = serializers.DateTimeField(allow_null=True)
    processed_at = serializers.DateTimeField(allow_null=True)
