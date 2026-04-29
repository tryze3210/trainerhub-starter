from __future__ import annotations

import uuid

from django.db import models
import django.db.models.deletion

from apps.trainers.models import TrainerProfile


class TrainerWallet(models.Model):
    """
    Legacy wallet table used by the already-applied payouts.0001 migration.

    v6.7 introduced a cleaner TrainerBalance/PayoutLedgerEntry naming model, but
    the live database still has TrainerWallet/BalanceEntry. To keep the project
    safe, payouts operations are implemented on top of these existing tables
    instead of forcing a destructive migration.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    currency = models.CharField(max_length=8, default="RUB")
    available_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pending_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    locked_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    trainer = models.OneToOneField(
        TrainerProfile,
        on_delete=django.db.models.deletion.CASCADE,
        related_name="wallet",
    )

    @property
    def trainer_id(self):
        return self.trainer.user_id

    @property
    def reserved_amount(self):
        return self.locked_amount

    @property
    def lifetime_earned_amount(self):
        # Best-effort calculated compatibility field for the v6 admin API.
        from django.db.models import Sum
        from django.db.models.functions import Coalesce
        from django.db.models import DecimalField, Value
        from decimal import Decimal

        return self.entries.filter(direction="credit").aggregate(
            total=Coalesce(
                Sum("amount"),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )["total"]

    def __str__(self):
        return f"Wallet<{self.trainer_id}> {self.currency}"


class BalanceEntryQuerySet(models.QuerySet):
    @staticmethod
    def _translate(kwargs: dict) -> dict:
        translated = dict(kwargs)
        if 'trainer_id' in translated:
            translated['wallet__trainer_id'] = translated.pop('trainer_id')
        if 'payment_id' in translated:
            translated['source_type'] = 'payment'
            translated['source_id'] = translated.pop('payment_id')
        if 'payout_request_id' in translated:
            translated['source_type'] = 'payout_request'
            translated['source_id'] = translated.pop('payout_request_id')
        return translated

    def filter(self, *args, **kwargs):
        return super().filter(*args, **self._translate(kwargs))

    def get(self, *args, **kwargs):
        return super().get(*args, **self._translate(kwargs))


class BalanceEntryManager(models.Manager.from_queryset(BalanceEntryQuerySet)):
    pass


class BalanceEntry(models.Model):
    class EntryType:
        ACCRUAL = "accrual"
        RESERVE = "reserve"
        RELEASE = "release"
        PAYOUT = "payout"
        ADJUSTMENT = "adjustment"
        SALE_CREDIT = "sale_credit"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    entry_type = models.CharField(max_length=32)
    direction = models.CharField(max_length=8)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="RUB")
    status = models.CharField(max_length=32, default="pending")
    source_type = models.CharField(max_length=32)
    source_id = models.UUIDField()

    objects = BalanceEntryManager()
    wallet = models.ForeignKey(
        TrainerWallet,
        on_delete=django.db.models.deletion.CASCADE,
        related_name="entries",
    )

    @property
    def trainer_id(self):
        return self.wallet.trainer.user_id

    @property
    def payment_id(self):
        return str(self.source_id) if self.source_type == "payment" else ""

    @property
    def payout_request_id(self):
        return self.source_id if self.source_type == "payout_request" else None

    @property
    def metadata(self):
        return {
            "direction": self.direction,
            "status": self.status,
            "source_type": self.source_type,
            "source_id": str(self.source_id),
            "wallet_id": str(self.wallet_id),
        }

    def __str__(self):
        return f"{self.entry_type} {self.direction} {self.amount} {self.currency}"


class PayoutRequest(models.Model):
    class Status:
        REQUESTED = "requested"
        PENDING = "pending"
        APPROVED = "approved"
        PROCESSING = "processing"
        PAID = "paid"
        REJECTED = "rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="RUB")
    status = models.CharField(max_length=32, default="requested")
    destination_json = models.JSONField(default=dict)
    trainer = models.ForeignKey(
        TrainerProfile,
        on_delete=django.db.models.deletion.PROTECT,
        related_name="payout_requests",
    )
    wallet = models.ForeignKey(
        TrainerWallet,
        on_delete=django.db.models.deletion.PROTECT,
    )

    @property
    def trainer_id(self):
        return self.trainer.user_id

    @property
    def destination_masked(self):
        data = self.destination_json or {}
        return data.get("destination_masked") or data.get("masked") or data.get("account_masked") or ""

    @property
    def requested_at(self):
        return self.created_at

    @property
    def approved_at(self):
        return (self.destination_json or {}).get("approved_at")

    @property
    def processed_at(self):
        return (self.destination_json or {}).get("processed_at")

    @property
    def rejected_reason(self):
        return (self.destination_json or {}).get("rejected_reason", "")

    @property
    def metadata(self):
        return self.destination_json or {}

    @property
    def ledger_entries(self):
        return self.wallet.entries.filter(source_type="payout_request", source_id=self.id).order_by("created_at")

    def __str__(self):
        return f"PayoutRequest<{self.id}> {self.status} {self.amount} {self.currency}"


# Compatibility aliases for v6 payout code. They intentionally do not register
# new Django models and therefore do not create unsafe migration drift.
TrainerBalance = TrainerWallet
PayoutLedgerEntry = BalanceEntry
