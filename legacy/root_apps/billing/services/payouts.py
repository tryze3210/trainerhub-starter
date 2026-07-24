from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.billing.domain.constants import LedgerAccount, LedgerDirection, LedgerSourceType, PayoutBatchStatus, PayoutItemStatus
from apps.billing.models import LedgerEntry, PayoutBatch, PayoutItem
from apps.billing.selectors.balances import TrainerBalanceSelector


class PayoutError(Exception):
    pass


class PayoutService:
    @classmethod
    @transaction.atomic
    def create_batch(cls, *, trainer, amount: Decimal | None = None, currency: str = "RUB") -> PayoutBatch:
        available = TrainerBalanceSelector.trainer_available_for_payout(trainer)
        if available <= Decimal("0.00"):
            raise PayoutError("No payout balance available")

        target_amount = min(amount or available, available)
        batch = PayoutBatch.objects.create(
            trainer=trainer,
            currency=currency,
            planned_amount=Decimal("0.00"),
        )

        running = Decimal("0.00")
        for entry in TrainerBalanceSelector.payout_candidates_queryset(trainer).order_by("event_at", "id"):
            if running >= target_amount:
                break
            remaining = target_amount - running
            allocation = min(entry.amount, remaining)
            PayoutItem.objects.create(
                batch=batch,
                ledger_entry=entry,
                amount=allocation,
            )
            running += allocation

        if running <= Decimal("0.00"):
            raise PayoutError("Payout batch allocation produced zero amount")

        batch.planned_amount = running
        batch.save(update_fields=["planned_amount", "updated_at"])
        return batch

    @classmethod
    @transaction.atomic
    def mark_processing(cls, *, batch: PayoutBatch, payout_reference: str) -> PayoutBatch:
        if batch.status != PayoutBatchStatus.DRAFT:
            raise PayoutError("Only draft payout batch can move to processing")
        batch.status = PayoutBatchStatus.PROCESSING
        batch.payout_reference = payout_reference
        batch.processed_at = timezone.now()
        batch.save(update_fields=["status", "payout_reference", "processed_at", "updated_at"])
        return batch

    @classmethod
    @transaction.atomic
    def mark_paid(cls, *, batch: PayoutBatch) -> PayoutBatch:
        if batch.status not in {PayoutBatchStatus.DRAFT, PayoutBatchStatus.PROCESSING}:
            raise PayoutError("Only draft/processing payout batch can be paid")

        payout_total = batch.items.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        if payout_total <= Decimal("0.00"):
            raise PayoutError("Cannot pay empty payout batch")

        for item in batch.items.select_related("ledger_entry").all():
            if item.status == PayoutItemStatus.PAID:
                continue
            LedgerEntry.objects.create(
                trainer=batch.trainer,
                user=item.ledger_entry.user,
                order=item.ledger_entry.order,
                order_item=item.ledger_entry.order_item,
                payment=item.ledger_entry.payment,
                subscription=item.ledger_entry.subscription,
                subscription_cycle=item.ledger_entry.subscription_cycle,
                entitlement=item.ledger_entry.entitlement,
                account=LedgerAccount.TRAINER_PAYABLE,
                direction=LedgerDirection.DEBIT,
                source_type=LedgerSourceType.PAYOUT,
                source_ref=str(batch.id),
                event_at=timezone.now(),
                currency=batch.currency,
                amount=item.amount,
                idempotency_key=f"ledger:payout:{batch.id}:item:{item.id}:trainer_payable_debit",
                group_key=f"payout:{batch.id}",
                metadata={"payout_reference": batch.payout_reference},
            )
            item.status = PayoutItemStatus.PAID
            item.save(update_fields=["status", "updated_at"])

        batch.status = PayoutBatchStatus.PAID
        batch.paid_at = timezone.now()
        batch.paid_amount = payout_total
        batch.save(update_fields=["status", "paid_at", "paid_amount", "updated_at"])
        return batch

    @classmethod
    @transaction.atomic
    def cancel_batch(cls, *, batch: PayoutBatch, reason: str) -> PayoutBatch:
        if batch.status == PayoutBatchStatus.PAID:
            raise PayoutError("Paid payout batch cannot be canceled")
        batch.status = PayoutBatchStatus.CANCELED
        batch.failure_reason = reason
        batch.save(update_fields=["status", "failure_reason", "updated_at"])
        return batch
