from decimal import Decimal
from django.db import models
from apps.common.db.models import TimeStampedModel


class TrainerBalance(TimeStampedModel):
    trainer_id = models.UUIDField(unique=True)
    currency = models.CharField(max_length=8, default='RUB')
    available_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    reserved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    lifetime_earned_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        db_table = 'payouts_trainer_balance'


class PayoutRequest(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        PROCESSING = 'processing', 'Processing'
        PAID = 'paid', 'Paid'
        REJECTED = 'rejected', 'Rejected'

    trainer_id = models.UUIDField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default='RUB')
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    destination_masked = models.CharField(max_length=128, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    rejected_reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'payouts_payout_request'
        indexes = [models.Index(fields=['trainer_id', 'status'])]


class PayoutLedgerEntry(TimeStampedModel):
    class EntryType(models.TextChoices):
        ACCRUAL = 'accrual', 'Accrual'
        RESERVE = 'reserve', 'Reserve'
        RELEASE = 'release', 'Release'
        PAYOUT = 'payout', 'Payout'
        ADJUSTMENT = 'adjustment', 'Adjustment'

    trainer_id = models.UUIDField()
    payout_request = models.ForeignKey(PayoutRequest, null=True, blank=True, on_delete=models.SET_NULL, related_name='ledger_entries')
    payment_id = models.CharField(max_length=64, blank=True)
    entry_type = models.CharField(max_length=32, choices=EntryType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default='RUB')
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'payouts_ledger_entry'
        indexes = [models.Index(fields=['trainer_id', 'entry_type'])]
