from django.conf import settings
from django.db import models
from django.utils import timezone

from .constants import (
    DOCUMENT_FORMATS,
    DOCUMENT_FORMAT_JSON,
    EXPORT_RUN_STATUSES,
    EXPORT_RUN_STATUS_DRAFT,
    JOURNAL_BATCH_STATUSES,
    JOURNAL_BATCH_STATUS_DRAFT,
    MAPPING_TARGETS,
)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ExternalAccountingSystem(TimeStampedModel):
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    adapter_key = models.CharField(max_length=128)
    base_currency = models.CharField(max_length=3, default="EUR")
    settings_json = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "accounting_external_system"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ChartOfAccount(TimeStampedModel):
    system = models.ForeignKey(
        ExternalAccountingSystem,
        on_delete=models.CASCADE,
        related_name="accounts",
    )
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=64)
    currency = models.CharField(max_length=3, default="EUR")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "accounting_chart_of_account"
        ordering = ["system_id", "code"]
        unique_together = [("system", "code")]

    def __str__(self) -> str:
        return f"{self.system.code}:{self.code}"


class AccountMappingRule(TimeStampedModel):
    system = models.ForeignKey(
        ExternalAccountingSystem,
        on_delete=models.CASCADE,
        related_name="mapping_rules",
    )
    target_type = models.CharField(max_length=64, choices=MAPPING_TARGETS)
    source_code = models.CharField(max_length=128)
    account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.PROTECT,
        related_name="mapping_rules",
    )
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    priority = models.PositiveSmallIntegerField(default=100)
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "accounting_account_mapping_rule"
        ordering = ["system_id", "target_type", "source_code", "priority"]
        indexes = [
            models.Index(fields=["system", "target_type", "source_code"]),
            models.Index(fields=["effective_from", "effective_to"]),
        ]


class JournalBatch(TimeStampedModel):
    system = models.ForeignKey(
        ExternalAccountingSystem,
        on_delete=models.PROTECT,
        related_name="journal_batches",
    )
    period = models.ForeignKey(
        "finance.ClosingPeriod",
        on_delete=models.PROTECT,
        related_name="journal_batches",
    )
    snapshot = models.ForeignKey(
        "finance.FinanceSnapshot",
        on_delete=models.PROTECT,
        related_name="journal_batches",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=32, choices=JOURNAL_BATCH_STATUSES, default=JOURNAL_BATCH_STATUS_DRAFT)
    batch_number = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=255)
    currency = models.CharField(max_length=3, default="EUR")
    total_debit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_credit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    finalized_at = models.DateTimeField(null=True, blank=True)
    exported_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_journal_batches",
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "accounting_journal_batch"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["system", "status"]),
            models.Index(fields=["period", "status"]),
        ]

    def mark_finalized(self):
        self.status = "finalized"
        self.finalized_at = timezone.now()

    def mark_exported(self):
        self.status = "exported"
        self.exported_at = timezone.now()


class JournalEntry(TimeStampedModel):
    batch = models.ForeignKey(
        JournalBatch,
        on_delete=models.CASCADE,
        related_name="entries",
    )
    entry_number = models.PositiveIntegerField()
    entry_date = models.DateField()
    reference = models.CharField(max_length=128)
    description = models.CharField(max_length=255)
    source_ledger_entry = models.ForeignKey(
        "finance.LedgerEntry",
        on_delete=models.PROTECT,
        related_name="journal_entries",
    )
    source_document = models.ForeignKey(
        "finance.AccountingDocument",
        on_delete=models.PROTECT,
        related_name="journal_entries",
        null=True,
        blank=True,
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "accounting_journal_entry"
        ordering = ["batch_id", "entry_number"]
        unique_together = [("batch", "entry_number")]


class JournalLine(TimeStampedModel):
    entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    line_number = models.PositiveIntegerField()
    account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.PROTECT,
        related_name="journal_lines",
    )
    debit_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="EUR")
    description = models.CharField(max_length=255, blank=True)
    dimensions = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "accounting_journal_line"
        ordering = ["entry_id", "line_number"]
        unique_together = [("entry", "line_number")]


class GLExportRun(TimeStampedModel):
    system = models.ForeignKey(
        ExternalAccountingSystem,
        on_delete=models.PROTECT,
        related_name="export_runs",
    )
    period = models.ForeignKey(
        "finance.ClosingPeriod",
        on_delete=models.PROTECT,
        related_name="gl_export_runs",
    )
    journal_batch = models.ForeignKey(
        JournalBatch,
        on_delete=models.PROTECT,
        related_name="export_runs",
    )
    export_format = models.CharField(max_length=16, choices=DOCUMENT_FORMATS, default=DOCUMENT_FORMAT_JSON)
    status = models.CharField(max_length=32, choices=EXPORT_RUN_STATUSES, default=EXPORT_RUN_STATUS_DRAFT)
    run_number = models.CharField(max_length=64, unique=True)
    idempotency_key = models.CharField(max_length=128, unique=True)
    payload = models.JSONField(default=dict, blank=True)
    file_path = models.CharField(max_length=512, blank=True)
    checksum = models.CharField(max_length=128, blank=True)
    exported_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)
    supersedes = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="superseded_by_runs",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_gl_export_runs",
    )

    class Meta:
        db_table = "accounting_gl_export_run"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["system", "period", "status"]),
            models.Index(fields=["journal_batch", "status"]),
        ]


class ExportDeliveryAttempt(TimeStampedModel):
    export_run = models.ForeignKey(
        GLExportRun,
        on_delete=models.CASCADE,
        related_name="delivery_attempts",
    )
    attempt_number = models.PositiveSmallIntegerField()
    request_payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    is_success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounting_export_delivery_attempt"
        ordering = ["export_run_id", "attempt_number"]
        unique_together = [("export_run", "attempt_number")]
