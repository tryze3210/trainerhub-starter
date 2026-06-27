import uuid
from django.conf import settings
from django.db import models


class TrainerFinanceProfile(models.Model):
    trainer = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="finance_profile")
    legal_name = models.CharField(max_length=255, blank=True)
    tax_number = models.CharField(max_length=64, blank=True)
    bank_name = models.CharField(max_length=255, blank=True)
    bank_account = models.CharField(max_length=128, blank=True)
    bank_bic = models.CharField(max_length=64, blank=True)
    payout_currency = models.CharField(max_length=16, default="RUB")
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "trainer_finance_profiles"


class FinanceDocument(models.Model):
    DOC_INVOICE = "invoice"
    DOC_RECEIPT = "receipt"
    DOC_CREDIT_NOTE = "credit_note"
    DOC_REFUND_DOCUMENT = "refund_document"
    DOC_PAYOUT_ACT = "payout_act"
    DOC_STATEMENT = "statement"
    DOC_CHOICES = [
        (DOC_INVOICE, "Invoice"),
        (DOC_RECEIPT, "Receipt"),
        (DOC_CREDIT_NOTE, "Credit Note"),
        (DOC_REFUND_DOCUMENT, "Refund Document"),
        (DOC_PAYOUT_ACT, "Payout Act"),
        (DOC_STATEMENT, "Statement"),
    ]

    STATUS_DRAFT = "draft"
    STATUS_FINALIZED = "finalized"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_FINALIZED, "Finalized"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trainer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="finance_documents")
    document_type = models.CharField(max_length=32, choices=DOC_CHOICES)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    period_start = models.DateField()
    period_end = models.DateField()
    document_number = models.CharField(max_length=64)
    currency = models.CharField(max_length=16, default="RUB")
    gross_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payload = models.JSONField(default=dict, blank=True)
    rendered_html = models.TextField(blank=True)
    artifact_path = models.CharField(max_length=512, blank=True)
    finalized_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "finance_documents"
        indexes = [
            models.Index(fields=["trainer", "document_type", "period_start", "period_end"]),
            models.Index(fields=["status", "created_at"]),
        ]
        ordering = ["-created_at"]
