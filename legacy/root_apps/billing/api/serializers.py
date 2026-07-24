from rest_framework import serializers

from apps.billing.models import LedgerEntry, PayoutBatch, PayoutItem, TrainerRevenuePolicy


class TrainerRevenuePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerRevenuePolicy
        fields = [
            "id",
            "trainer",
            "scope",
            "order_item_type",
            "subscription_plan_code",
            "trainer_share_percent",
            "platform_commission_percent",
            "is_active",
            "effective_from",
            "effective_to",
            "priority",
            "created_at",
            "updated_at",
        ]


class LedgerEntrySerializer(serializers.ModelSerializer):
    signed_amount = serializers.SerializerMethodField()

    class Meta:
        model = LedgerEntry
        fields = [
            "id",
            "trainer",
            "user",
            "order",
            "order_item",
            "payment",
            "refund",
            "subscription",
            "subscription_cycle",
            "entitlement",
            "account",
            "direction",
            "source_type",
            "source_ref",
            "event_at",
            "currency",
            "amount",
            "signed_amount",
            "group_key",
            "reversal_of",
            "metadata",
            "notes",
            "created_at",
        ]

    def get_signed_amount(self, obj):
        return obj.signed_amount()


class PayoutItemSerializer(serializers.ModelSerializer):
    ledger_entry = LedgerEntrySerializer(read_only=True)

    class Meta:
        model = PayoutItem
        fields = ["id", "ledger_entry", "status", "amount", "created_at", "updated_at"]


class PayoutBatchSerializer(serializers.ModelSerializer):
    items = PayoutItemSerializer(many=True, read_only=True)

    class Meta:
        model = PayoutBatch
        fields = [
            "id",
            "trainer",
            "status",
            "currency",
            "planned_amount",
            "paid_amount",
            "payout_reference",
            "processed_at",
            "paid_at",
            "failure_reason",
            "metadata",
            "items",
            "created_at",
            "updated_at",
        ]


class CreatePayoutBatchSerializer(serializers.Serializer):
    trainer_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    currency = serializers.CharField(max_length=8, required=False, default="RUB")


class TransitionPayoutBatchSerializer(serializers.Serializer):
    payout_reference = serializers.CharField(max_length=128, required=False, allow_blank=False)
    reason = serializers.CharField(max_length=255, required=False, allow_blank=False)
