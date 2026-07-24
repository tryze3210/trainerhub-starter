from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from apps.billing.domain.constants import (
    LedgerAccount,
    LedgerDirection,
    LedgerSourceType,
    PayoutBatchStatus,
    PayoutItemStatus,
    RevenuePolicyScope,
)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TrainerRevenuePolicy(TimeStampedModel):
    trainer = models.ForeignKey(
        "trainers.TrainerProfile",
        on_delete=models.CASCADE,
        related_name="revenue_policies",
    )
    scope = models.CharField(max_length=32, choices=RevenuePolicyScope.choices, default=RevenuePolicyScope.TRAINER)
    order_item_type = models.CharField(max_length=64, blank=True)
    subscription_plan_code = models.CharField(max_length=64, blank=True)
    trainer_share_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))],
    )
    platform_commission_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))],
    )
    is_active = models.BooleanField(default=True)
    effective_from = models.DateTimeField(default=timezone.now)
    effective_to = models.DateTimeField(blank=True, null=True)
    priority = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ["priority", "-effective_from", "id"]
        indexes = [
            models.Index(fields=["trainer", "is_active"]),
            models.Index(fields=["trainer", "scope", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"Policy<{self.trainer_id}:{self.scope}:{self.trainer_share_percent}/{self.platform_commission_percent}>"


class LedgerEntry(TimeStampedModel):
    trainer = models.ForeignKey(
        "trainers.TrainerProfile",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="ledger_entries",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="billing_ledger_entries",
    )
    order = models.ForeignKey("orders.Order", on_delete=models.SET_NULL, blank=True, null=True, related_name="ledger_entries")
    order_item = models.ForeignKey(
        "orders.OrderItem",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="ledger_entries",
    )
    payment = models.ForeignKey("payments.Payment", on_delete=models.SET_NULL, blank=True, null=True, related_name="ledger_entries")
    refund = models.ForeignKey("payments.Refund", on_delete=models.SET_NULL, blank=True, null=True, related_name="ledger_entries")
    subscription = models.ForeignKey(
        "subscriptions.Subscription",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="ledger_entries",
    )
    subscription_cycle = models.ForeignKey(
        "subscriptions.SubscriptionCycle",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="ledger_entries",
    )
    entitlement = models.ForeignKey(
        "entitlements.Entitlement",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="ledger_entries",
    )

    account = models.CharField(max_length=64, choices=LedgerAccount.choices)
    direction = models.CharField(max_length=16, choices=LedgerDirection.choices)
    source_type = models.CharField(max_length=64, choices=LedgerSourceType.choices)
    source_ref = models.CharField(max_length=128, db_index=True)
    event_at = models.DateTimeField(default=timezone.now, db_index=True)

    currency = models.CharField(max_length=8, default="RUB")
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    idempotency_key = models.CharField(max_length=128, unique=True)
    group_key = models.CharField(max_length=128, db_index=True)
    reversal_of = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="reversal_entries",
    )

    metadata = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-event_at", "-id"]
        indexes = [
            models.Index(fields=["trainer", "account", "event_at"]),
            models.Index(fields=["payment", "account"]),
            models.Index(fields=["subscription", "subscription_cycle"]),
            models.Index(fields=["source_type", "source_ref"]),
            models.Index(fields=["group_key"]),
        ]

    def signed_amount(self) -> Decimal:
        sign = Decimal("1.00") if self.direction == LedgerDirection.CREDIT else Decimal("-1.00")
        return sign * self.amount

    def __str__(self) -> str:
        return f"LedgerEntry<{self.id}:{self.account}:{self.direction}:{self.amount}>"


class PayoutBatch(TimeStampedModel):
    trainer = models.ForeignKey(
        "trainers.TrainerProfile",
        on_delete=models.CASCADE,
        related_name="payout_batches",
    )
    status = models.CharField(max_length=24, choices=PayoutBatchStatus.choices, default=PayoutBatchStatus.DRAFT)
    currency = models.CharField(max_length=8, default="RUB")
    planned_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    payout_reference = models.CharField(max_length=128, blank=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    failure_reason = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["trainer", "status"])]


class PayoutItem(TimeStampedModel):
    batch = models.ForeignKey(PayoutBatch, on_delete=models.CASCADE, related_name="items")
    ledger_entry = models.OneToOneField(LedgerEntry, on_delete=models.PROTECT, related_name="payout_item")
    status = models.CharField(max_length=24, choices=PayoutItemStatus.choices, default=PayoutItemStatus.ALLOCATED)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reversal_entry = models.ForeignKey(
        LedgerEntry,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="reversed_payout_items",
    )

    class Meta:
        indexes = [models.Index(fields=["status"])]
        constraints = [
            models.CheckConstraint(check=models.Q(amount__gt=0), name="billing_payout_item_amount_gt_zero"),
        ]
