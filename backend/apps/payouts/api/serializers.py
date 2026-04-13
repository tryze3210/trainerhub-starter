from rest_framework import serializers
from apps.payouts.models import TrainerBalance, PayoutRequest


class TrainerBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerBalance
        fields = ['trainer_id', 'currency', 'available_amount', 'reserved_amount', 'lifetime_earned_amount', 'updated_at']


class PayoutRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayoutRequest
        fields = [
            'id', 'trainer_id', 'amount', 'currency', 'status', 'destination_masked',
            'requested_at', 'approved_at', 'processed_at', 'rejected_reason', 'metadata', 'created_at'
        ]


class CreatePayoutRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    destination_masked = serializers.CharField(max_length=128)
