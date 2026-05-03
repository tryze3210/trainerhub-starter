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


def _normalize_uuidish(value):
    """Normalize legacy UUID-like values for source_id lookups."""
    return str(value) if value is not None else value


class BalanceEntryQuerySet(models.QuerySet):
    """
    Compatibility layer for old payout ledger code/tests.

    Canonical ledger rows use source_type/source_id and wallet -> trainer joins.
    Older code still queries virtual fields like payment_id or trainer_id. This
    queryset rewrites those filters without adding fake database columns.
    """

    LEGACY_SOURCE_FILTERS = {
        "payment_id": "payment",
        "payout_request_id": "payout_request",
        "refund_payment_id": "payment_refund",
        "chargeback_payment_id": "payment_chargeback",
    }

    def _rewrite_legacy_kwargs(self, kwargs):
        rewritten = dict(kwargs)

        trainer_id = rewritten.pop("trainer_id", None)
        if trainer_id is not None:
            rewritten.setdefault("wallet__trainer_id", trainer_id)

        trainer_user_id = rewritten.pop("trainer_user_id", None)
        if trainer_user_id is not None:
            rewritten.setdefault("wallet__trainer__user_id", trainer_user_id)

        for legacy_key, source_type in self.LEGACY_SOURCE_FILTERS.items():
            value = rewritten.pop(legacy_key, None)
            if value is not None:
                rewritten.setdefault("source_id", _normalize_uuidish(value))
                rewritten.setdefault("source_type", source_type)

        return rewritten

    def filter(self, *args, **kwargs):
        return super().filter(*args, **self._rewrite_legacy_kwargs(kwargs))

    def exclude(self, *args, **kwargs):
        return super().exclude(*args, **self._rewrite_legacy_kwargs(kwargs))

    def get(self, *args, **kwargs):
        return super().get(*args, **self._rewrite_legacy_kwargs(kwargs))

    def get_or_create(self, defaults=None, **kwargs):
        return super().get_or_create(defaults=defaults, **self._rewrite_legacy_kwargs(kwargs))

    def update_or_create(self, defaults=None, create_defaults=None, **kwargs):
        return super().update_or_create(
            defaults=defaults,
            create_defaults=create_defaults,
            **self._rewrite_legacy_kwargs(kwargs),
        )


class BalanceEntry(models.Model):
    class EntryType:
        ACCRUAL = "accrual"
        RESERVE = "reserve"
        RELEASE = "release"
        PAYOUT = "payout"
        ADJUSTMENT = "adjustment"
        SALE_CREDIT = "sale_credit"
        REVERSAL = "reversal"
        RISK_HOLD = "risk_hold"
        RISK_HOLD_RELEASE = "risk_hold_release"
        RISK_HOLD_CONSUMED = "risk_hold_consumed"

    objects = BalanceEntryQuerySet.as_manager()

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
