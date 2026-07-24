from rest_framework import serializers

from apps.entitlements.models import EntitlementStatus
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


class AdminPaymentSerializer(PaymentSerializer):
    buyer_email = serializers.SerializerMethodField()
    buyer_id = serializers.SerializerMethodField()
    order_status = serializers.CharField(source='order.status', read_only=True)
    order_type = serializers.CharField(source='order.order_type', read_only=True)
    order_total_amount = serializers.DecimalField(source='order.total_amount', max_digits=12, decimal_places=2, read_only=True)
    refund_operations = serializers.SerializerMethodField()
    entitlement_summary = serializers.SerializerMethodField()

    class Meta(PaymentSerializer.Meta):
        fields = PaymentSerializer.Meta.fields + [
            'buyer_id',
            'buyer_email',
            'order_status',
            'order_type',
            'order_total_amount',
            'refund_operations',
            'entitlement_summary',
        ]

    def get_buyer_id(self, obj):
        return str(obj.order.user_id) if obj.order_id else ''

    def get_buyer_email(self, obj):
        return getattr(obj.order.user, 'email', '') if obj.order_id else ''

    def get_refund_operations(self, obj):
        operations = (obj.provider_payload or {}).get('refund_operations') or []
        return operations if isinstance(operations, list) else []

    def get_entitlement_summary(self, obj):
        entitlements = list(getattr(obj.order, 'granted_entitlements', []).all())
        active = sum(1 for item in entitlements if item.status == EntitlementStatus.ACTIVE)
        revoked = sum(1 for item in entitlements if item.status == EntitlementStatus.REVOKED)
        expired = sum(1 for item in entitlements if item.status == EntitlementStatus.EXPIRED)
        total = len(entitlements)

        if active:
            status = 'active'
        elif revoked:
            status = 'revoked'
        elif expired:
            status = 'expired'
        elif obj.status == 'succeeded':
            status = 'missing'
        else:
            status = 'not_granted'

        return {
            'status': status,
            'total': total,
            'active': active,
            'revoked': revoked,
            'expired': expired,
        }


class PaymentWebhookSerializer(serializers.Serializer):
    provider = serializers.CharField()
    event_type = serializers.CharField()
    external_event_id = serializers.CharField()
    payload = serializers.JSONField()
    headers = serializers.JSONField(required=False)
    signature = serializers.CharField(required=False, allow_blank=True)
    raw_payload_hash = serializers.CharField(required=False, allow_blank=True)


class PaymentRefundSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    refund_id = serializers.CharField(required=False, allow_blank=True)
    reason = serializers.CharField(required=False, allow_blank=True)


class PaymentWebhookEventSerializer(serializers.ModelSerializer):
    payment_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = PaymentWebhookEvent
        fields = [
            'id',
            'provider',
            'event_type',
            'external_event_id',
            'provider_event_id',
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
