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


class PayoutProjectionRunSerializer(serializers.Serializer):
    batch_size = serializers.IntegerField(required=False, min_value=1, max_value=500, default=100)


class PayoutLedgerCountSerializer(serializers.Serializer):
    entry_type = serializers.CharField()
    currency = serializers.CharField()
    count = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)


class PayoutProjectionHealthSerializer(serializers.Serializer):
    consumer = serializers.CharField()
    status = serializers.CharField()
    projected_messages = serializers.IntegerField()
    skipped_messages = serializers.IntegerField()
    failed_messages = serializers.IntegerField()
    latest_processed_at = serializers.DateTimeField(allow_null=True)
    latest_message_key = serializers.CharField(allow_blank=True)
    latest_payload = serializers.DictField()
    ledger_accrual_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    ledger_counts = PayoutLedgerCountSerializer(many=True)


class PayoutRiskHoldSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    payment_id = serializers.SerializerMethodField()
    trainer_id = serializers.SerializerMethodField()
    wallet_id = serializers.SerializerMethodField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    status = serializers.CharField()
    source_type = serializers.CharField()
    released_amount = serializers.SerializerMethodField()
    consumed_amount = serializers.SerializerMethodField()
    active_amount = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    def _sum_related(self, obj: BalanceEntry, *, entry_type: str) -> Decimal:
        total = Decimal("0.00")
        entries = BalanceEntry.objects.filter(
            wallet=obj.wallet,
            source_id=obj.source_id,
            entry_type=entry_type,
        )
        for entry in entries:
            total += entry.amount
        return total

    def get_payment_id(self, obj: BalanceEntry):
        return str(obj.source_id)

    def get_trainer_id(self, obj: BalanceEntry):
        return str(obj.wallet.trainer.user_id)

    def get_wallet_id(self, obj: BalanceEntry):
        return str(obj.wallet_id)

    def get_released_amount(self, obj: BalanceEntry):
        return self._sum_related(obj, entry_type=BalanceEntry.EntryType.RISK_HOLD_RELEASE)

    def get_consumed_amount(self, obj: BalanceEntry):
        return self._sum_related(obj, entry_type=BalanceEntry.EntryType.RISK_HOLD_CONSUMED)

    def get_active_amount(self, obj: BalanceEntry):
        return max(
            obj.amount - self.get_released_amount(obj) - self.get_consumed_amount(obj),
            Decimal("0.00"),
        )


class PayoutRiskHoldReportSerializer(serializers.Serializer):
    status = serializers.CharField()
    active_hold_count = serializers.IntegerField()
    active_hold_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    released_hold_count = serializers.IntegerField()
    consumed_hold_count = serializers.IntegerField()
    shortfall_count = serializers.IntegerField()
    recent_holds = PayoutRiskHoldSerializer(many=True)


class ManualPaymentHoldReleaseSerializer(serializers.Serializer):
    payment_id = serializers.UUIDField()
    reason = serializers.CharField(required=False, allow_blank=True, default="manual_ops_release")
