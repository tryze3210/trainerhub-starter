import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from .domain.enums import (
    DiscrepancyStatus,
    DiscrepancyType,
    OutboxEventStatus,
    ReconciliationSessionStatus,
    SettlementDirection,
    SettlementProvider,
    SettlementStatus,
)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SettlementTransaction(TimeStampedModel):
    """
    Normalized provider-facing settlement entity.
    Does not replace ledger entries; it tracks external movement state.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.CharField(max_length=32, choices=SettlementProvider.choices)
    direction = models.CharField(max_length=32, choices=SettlementDirection.choices)
    status = models.CharField(max_length=32, choices=SettlementStatus.choices, default=SettlementStatus.PENDING)

    payout_batch = models.ForeignKey(
        "payouts.PayoutBatch",
        on_delete=models.PROTECT,
        related_name="settlement_transactions",
        null=True,
        blank=True,
    )
    payout_item = models.ForeignKey(
        "payouts.PayoutItem",
        on_delete=models.PROTECT,
        related_name="settlement_transactions",
        null=True,
        blank=True,
    )
    trainer = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="settlement_transactions",
        null=True,
        blank=True,
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="RUB")

    provider_reference = models.CharField(max_length=128, db_index=True)
    provider_batch_reference = models.CharField(max_length=128, blank=True)
    idempotency_key = models.CharField(max_length=128, unique=True)

    requested_at = models.DateTimeField(default=timezone.now)
    settled_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)

    provider_payload = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "finance_settlement_transactions"
        indexes = [
            models.Index(fields=["provider", "status"]),
            models.Index(fields=["provider_reference"]),
            models.Index(fields=["requested_at"]),
        ]


class ReconciliationSession(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.CharField(max_length=32, choices=SettlementProvider.choices)
    status = models.CharField(
        max_length=32,
        choices=ReconciliationSessionStatus.choices,
        default=ReconciliationSessionStatus.RUNNING,
    )
    date_from = models.DateTimeField()
    date_to = models.DateTimeField()
    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="started_reconciliation_sessions",
        null=True,
        blank=True,
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    summary = models.JSONField(default=dict, blank=True)
    raw_import_meta = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "finance_reconciliation_sessions"
        indexes = [models.Index(fields=["provider", "status"])]


class ReconciliationDiscrepancy(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        ReconciliationSession,
        on_delete=models.CASCADE,
        related_name="discrepancies",
    )
    discrepancy_type = models.CharField(max_length=32, choices=DiscrepancyType.choices)
    status = models.CharField(max_length=32, choices=DiscrepancyStatus.choices, default=DiscrepancyStatus.OPEN)

    settlement_transaction = models.ForeignKey(
        SettlementTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="discrepancies",
    )
    internal_reference = models.CharField(max_length=128, blank=True)
    provider_reference = models.CharField(max_length=128, blank=True)

    internal_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    provider_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    internal_status = models.CharField(max_length=64, blank=True)
    provider_status = models.CharField(max_length=64, blank=True)

    details = models.JSONField(default=dict, blank=True)
    resolution_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="resolved_finance_discrepancies",
        null=True,
        blank=True,
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "finance_reconciliation_discrepancies"
        indexes = [
            models.Index(fields=["status", "discrepancy_type"]),
            models.Index(fields=["provider_reference"]),
        ]


class FinanceOutboxEvent(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.CharField(max_length=128, db_index=True)
    aggregate_type = models.CharField(max_length=64)
    aggregate_id = models.CharField(max_length=64)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=32, choices=OutboxEventStatus.choices, default=OutboxEventStatus.PENDING)
    available_at = models.DateTimeField(default=timezone.now)
    delivered_at = models.DateTimeField(null=True, blank=True)
    fail_count = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)

    class Meta:
        db_table = "finance_outbox_events"
        indexes = [
            models.Index(fields=["status", "available_at"]),
            models.Index(fields=["topic", "status"]),
        ]


class ProviderWebhookInbox(TimeStampedModel):
    """
    Raw incoming provider event registry for idempotent processing.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.CharField(max_length=32, choices=SettlementProvider.choices)
    event_id = models.CharField(max_length=128, unique=True)
    event_type = models.CharField(max_length=128)
    payload = models.JSONField(default=dict)
    signature_valid = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_error = models.TextField(blank=True)

    class Meta:
        db_table = "finance_provider_webhook_inbox"
        indexes = [models.Index(fields=["provider", "event_type"])]
