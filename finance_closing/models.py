import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from .constants import (
    AccountingDocumentStatus,
    AccountingDocumentType,
    ClosingPeriodStatus,
    SnapshotStatus,
)


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ClosingPeriod(TimestampedModel):
    """
    Immutable business period boundaries for finance close.
    One row per month/currency/legal entity.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=32, unique=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    currency = models.CharField(max_length=8)
    legal_entity_code = models.CharField(max_length=64, default='platform-main')
    status = models.CharField(max_length=32, choices=ClosingPeriodStatus.choices, default=ClosingPeriodStatus.OPEN)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='finance_closed_periods',
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-starts_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['currency', 'legal_entity_code']),
        ]


class FinanceSnapshot(TimestampedModel):
    """
    Denormalized month-end snapshot for dashboard and statement generation.
    Snapshot is append-only; latest READY snapshot for a period is authoritative.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    period = models.ForeignKey(ClosingPeriod, on_delete=models.PROTECT, related_name='snapshots')
    status = models.CharField(max_length=16, choices=SnapshotStatus.choices, default=SnapshotStatus.PENDING)
    version = models.PositiveIntegerField(default=1)
    ledger_cutoff_at = models.DateTimeField()
    payload = models.JSONField(default=dict, blank=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='generated_finance_snapshots',
    )

    class Meta:
        ordering = ['-created_at']
        unique_together = [('period', 'version')]


class AccountingDocument(TimestampedModel):
    """
    Statement / invoice / credit-note registry.
    Document body is frozen at issue time.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document_type = models.CharField(max_length=32, choices=AccountingDocumentType.choices)
    status = models.CharField(max_length=16, choices=AccountingDocumentStatus.choices, default=AccountingDocumentStatus.DRAFT)
    number = models.CharField(max_length=64, unique=True)
    period = models.ForeignKey(ClosingPeriod, on_delete=models.PROTECT, related_name='documents')
    trainer = models.ForeignKey('trainers.Trainer', null=True, blank=True, on_delete=models.PROTECT, related_name='accounting_documents')
    currency = models.CharField(max_length=8)
    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    issued_at = models.DateTimeField(null=True, blank=True)
    voided_at = models.DateTimeField(null=True, blank=True)
    replaces_document = models.ForeignKey('self', null=True, blank=True, on_delete=models.PROTECT, related_name='replacement_documents')
    payload = models.JSONField(default=dict, blank=True)
    rendered_file = models.FileField(upload_to='finance-documents/%Y/%m/', null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document_type', 'status']),
            models.Index(fields=['trainer', 'period']),
        ]


class AccountingDocumentLine(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(AccountingDocument, on_delete=models.CASCADE, related_name='lines')
    sort_order = models.PositiveIntegerField(default=0)
    code = models.CharField(max_length=64)
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('1.00'))
    unit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    line_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['sort_order', 'created_at']


class TrainerMonthStatement(TimestampedModel):
    """
    One statement per trainer/period/currency. Backed by snapshot + frozen lines.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trainer = models.ForeignKey('trainers.Trainer', on_delete=models.PROTECT, related_name='month_statements')
    period = models.ForeignKey(ClosingPeriod, on_delete=models.PROTECT, related_name='trainer_statements')
    snapshot = models.ForeignKey(FinanceSnapshot, on_delete=models.PROTECT, related_name='trainer_statements')
    accounting_document = models.OneToOneField(AccountingDocument, null=True, blank=True, on_delete=models.SET_NULL, related_name='trainer_statement')
    currency = models.CharField(max_length=8)
    gross_sales_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    refunds_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    payout_fees_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    reserve_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    net_payable_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    line_items = models.JSONField(default=list, blank=True)
    issued_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [('trainer', 'period', 'currency')]
        indexes = [models.Index(fields=['trainer', 'period'])]


class TaxProfile(TimestampedModel):
    trainer = models.OneToOneField('trainers.Trainer', on_delete=models.CASCADE, related_name='tax_profile')
    country_code = models.CharField(max_length=2)
    tax_number = models.CharField(max_length=128, blank=True)
    vat_number = models.CharField(max_length=128, blank=True)
    withholding_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    is_company = models.BooleanField(default=False)
    legal_name = models.CharField(max_length=255, blank=True)
    address = models.JSONField(default=dict, blank=True)


class FinanceCloseAuditLog(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    period = models.ForeignKey(ClosingPeriod, on_delete=models.CASCADE, related_name='audit_logs')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=128)
    details = models.JSONField(default=dict, blank=True)


class ClosingGuardFailure(Exception):
    pass
