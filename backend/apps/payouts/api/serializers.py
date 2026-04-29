from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.payouts.models import BalanceEntry, PayoutRequest, TrainerWallet


class TrainerBalanceSerializer(serializers.Serializer):
    trainer_id = serializers.SerializerMethodField()
    currency = serializers.CharField()
    available_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    reserved_amount = serializers.SerializerMethodField()
    lifetime_earned_amount = serializers.SerializerMethodField()
    updated_at = serializers.DateTimeField()

    def get_trainer_id(self, obj: TrainerWallet):
        return str(obj.trainer.user_id)

    def get_reserved_amount(self, obj: TrainerWallet):
        return obj.locked_amount

    def get_lifetime_earned_amount(self, obj: TrainerWallet):
        return obj.lifetime_earned_amount or Decimal("0.00")


class PayoutLedgerEntrySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    payout_request = serializers.SerializerMethodField()
    payment_id = serializers.SerializerMethodField()
    entry_type = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    metadata = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    def get_payout_request(self, obj: BalanceEntry):
        return str(obj.source_id) if obj.source_type == "payout_request" else None

    def get_payment_id(self, obj: BalanceEntry):
        return str(obj.source_id) if obj.source_type == "payment" else ""

    def get_metadata(self, obj: BalanceEntry):
        return obj.metadata


class PayoutRequestSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    trainer_id = serializers.SerializerMethodField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    status = serializers.SerializerMethodField()
    destination_masked = serializers.SerializerMethodField()
    requested_at = serializers.DateTimeField(source="created_at")
    approved_at = serializers.SerializerMethodField()
    processed_at = serializers.SerializerMethodField()
    rejected_reason = serializers.SerializerMethodField()
    metadata = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    def get_trainer_id(self, obj: PayoutRequest):
        return str(obj.trainer.user_id)

    def get_status(self, obj: PayoutRequest):
        # Normalize the original v1 status for the new admin UI.
        return PayoutRequest.Status.PENDING if obj.status == PayoutRequest.Status.REQUESTED else obj.status

    def get_destination_masked(self, obj: PayoutRequest):
        return obj.destination_masked

    def get_approved_at(self, obj: PayoutRequest):
        return (obj.destination_json or {}).get("approved_at")

    def get_processed_at(self, obj: PayoutRequest):
        return (obj.destination_json or {}).get("processed_at")

    def get_rejected_reason(self, obj: PayoutRequest):
        return (obj.destination_json or {}).get("rejected_reason", "")

    def get_metadata(self, obj: PayoutRequest):
        return obj.destination_json or {}


class PayoutRequestDetailSerializer(PayoutRequestSerializer):
    ledger_entries = serializers.SerializerMethodField()

    def get_ledger_entries(self, obj: PayoutRequest):
        entries = obj.wallet.entries.filter(source_type="payout_request", source_id=obj.id).order_by("created_at")
        return PayoutLedgerEntrySerializer(entries, many=True).data


class CreatePayoutRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    destination_masked = serializers.CharField(max_length=128)


class AdminPayoutDecisionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["approve", "processing", "paid", "reject"])
    reason = serializers.CharField(required=False, allow_blank=True, default="")
    external_reference = serializers.CharField(required=False, allow_blank=True, default="")


class AdminPayoutBulkTransitionSerializer(AdminPayoutDecisionSerializer):
    payout_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1, max_length=100)


class AdminPayoutRepairSerializer(serializers.Serializer):
    dry_run = serializers.BooleanField(required=False, default=True)


class PayoutStatusBucketSerializer(serializers.Serializer):
    status = serializers.CharField()
    count = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)


class PayoutLedgerBucketSerializer(serializers.Serializer):
    entry_type = serializers.CharField()
    count = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)


class PayoutBalanceTotalsSerializer(serializers.Serializer):
    available_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    reserved_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    lifetime_earned_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    trainers_count = serializers.IntegerField()


class PayoutOpsSummarySerializer(serializers.Serializer):
    pending_exposure_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    pending_exposure_count = serializers.IntegerField()
    reserved_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    available_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    reconciliation_status = serializers.CharField(required=False)
    reconciliation_issue_count = serializers.IntegerField(required=False)


class AdminPayoutOverviewSerializer(serializers.Serializer):
    statuses = PayoutStatusBucketSerializer(many=True)
    ledger = PayoutLedgerBucketSerializer(many=True)
    balances = PayoutBalanceTotalsSerializer()
    ops = PayoutOpsSummarySerializer()
    recent_requests = PayoutRequestSerializer(many=True)
