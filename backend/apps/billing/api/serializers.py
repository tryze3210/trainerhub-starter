from rest_framework import serializers
from apps.billing.models import CheckoutSession


class CreateCheckoutSessionSerializer(serializers.Serializer):
    checkout_type = serializers.ChoiceField(choices=[CheckoutSession.CheckoutType.SUBSCRIPTION])
    target_id = serializers.CharField()
    success_url = serializers.URLField(required=False, allow_blank=True)
    cancel_url = serializers.URLField(required=False, allow_blank=True)


class CheckoutSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckoutSession
        fields = [
            'id', 'checkout_type', 'target_id', 'currency', 'gross_amount', 'status',
            'provider', 'provider_session_id', 'success_url', 'cancel_url', 'expires_at', 'metadata', 'created_at'
        ]
