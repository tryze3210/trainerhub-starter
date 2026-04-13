from django.db import models


class PayoutBatchStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    EXPORTED = "exported", "Exported"
    PROCESSING = "processing", "Processing"
    PAID = "paid", "Paid"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class SettlementProvider(models.TextChoices):
    MANUAL = "manual", "Manual"
    YOOKASSA = "yookassa", "YooKassa"
    STRIPE = "stripe", "Stripe"
    ADYEN = "adyen", "Adyen"
    TINKOFF = "tinkoff", "Tinkoff"


class SettlementDirection(models.TextChoices):
    PAYOUT = "payout", "Payout"
    REFUND = "refund", "Refund"
    CHARGEBACK = "chargeback", "Chargeback"
    ADJUSTMENT = "adjustment", "Adjustment"


class SettlementStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    PROCESSING = "processing", "Processing"
    SETTLED = "settled", "Settled"
    FAILED = "failed", "Failed"
    REVERSED = "reversed", "Reversed"


class ReconciliationSessionStatus(models.TextChoices):
    RUNNING = "running", "Running"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class DiscrepancyType(models.TextChoices):
    MISSING_INTERNAL = "missing_internal", "Missing internal"
    MISSING_PROVIDER = "missing_provider", "Missing provider"
    AMOUNT_MISMATCH = "amount_mismatch", "Amount mismatch"
    STATUS_MISMATCH = "status_mismatch", "Status mismatch"
    DUPLICATE_PROVIDER = "duplicate_provider", "Duplicate provider"
    DUPLICATE_INTERNAL = "duplicate_internal", "Duplicate internal"


class DiscrepancyStatus(models.TextChoices):
    OPEN = "open", "Open"
    ACKNOWLEDGED = "acknowledged", "Acknowledged"
    RESOLVED = "resolved", "Resolved"
    IGNORED = "ignored", "Ignored"


class OutboxEventStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    DELIVERED = "delivered", "Delivered"
    FAILED = "failed", "Failed"
