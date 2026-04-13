from django.db import models


class AccountingDocumentType(models.TextChoices):
    TRAINER_STATEMENT = 'trainer_statement', 'Trainer statement'
    PLATFORM_INVOICE = 'platform_invoice', 'Platform invoice'
    CREDIT_NOTE = 'credit_note', 'Credit note'


class AccountingDocumentStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    ISSUED = 'issued', 'Issued'
    VOID = 'void', 'Void'


class ClosingPeriodStatus(models.TextChoices):
    OPEN = 'open', 'Open'
    CLOSING = 'closing', 'Closing'
    CLOSED = 'closed', 'Closed'
    REOPENED = 'reopened', 'Reopened'


class SnapshotStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    READY = 'ready', 'Ready'
    SUPERSEDED = 'superseded', 'Superseded'
