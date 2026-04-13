from django.db import models


class LedgerAccount(models.TextChoices):
    CASH_IN = "cash_in", "Customer Cash In"
    TRAINER_PAYABLE = "trainer_payable", "Trainer Payable"
    PLATFORM_COMMISSION_REVENUE = "platform_commission_revenue", "Platform Commission Revenue"
    REFUND_LIABILITY = "refund_liability", "Refund Liability"
    PAYOUT_CLEARING = "payout_clearing", "Payout Clearing"
    PROCESSOR_FEE_EXPENSE = "processor_fee_expense", "Processor Fee Expense"
    TAX_PAYABLE = "tax_payable", "Tax Payable"


class LedgerDirection(models.TextChoices):
    DEBIT = "debit", "Debit"
    CREDIT = "credit", "Credit"


class LedgerSourceType(models.TextChoices):
    ORDER_PAYMENT = "order_payment", "Order Payment"
    SUBSCRIPTION_PAYMENT = "subscription_payment", "Subscription Payment"
    REFUND = "refund", "Refund"
    ENTITLEMENT_REVERSAL = "entitlement_reversal", "Entitlement Reversal"
    PAYOUT = "payout", "Payout"
    MANUAL_ADJUSTMENT = "manual_adjustment", "Manual Adjustment"


class PayoutBatchStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PROCESSING = "processing", "Processing"
    PAID = "paid", "Paid"
    FAILED = "failed", "Failed"
    CANCELED = "canceled", "Canceled"


class PayoutItemStatus(models.TextChoices):
    ALLOCATED = "allocated", "Allocated"
    PAID = "paid", "Paid"
    REVERSED = "reversed", "Reversed"


class RevenuePolicyScope(models.TextChoices):
    DEFAULT = "default", "Default"
    TRAINER = "trainer", "Trainer"
    PRODUCT = "product", "Product"
    SUBSCRIPTION_PLAN = "subscription_plan", "Subscription Plan"
