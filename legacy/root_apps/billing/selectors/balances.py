from __future__ import annotations

from decimal import Decimal

from django.db.models import F, Q, Sum, Value
from django.db.models.functions import Coalesce

from apps.billing.domain.constants import LedgerAccount, LedgerDirection
from apps.billing.models import LedgerEntry, PayoutItem


class TrainerBalanceSelector:
    @staticmethod
    def trainer_payable_balance(trainer) -> Decimal:
        credit_sum = LedgerEntry.objects.filter(
            trainer=trainer,
            account=LedgerAccount.TRAINER_PAYABLE,
            direction=LedgerDirection.CREDIT,
        ).aggregate(total=Coalesce(Sum("amount"), Value(Decimal("0.00"))))["total"]

        debit_sum = LedgerEntry.objects.filter(
            trainer=trainer,
            account=LedgerAccount.TRAINER_PAYABLE,
            direction=LedgerDirection.DEBIT,
        ).aggregate(total=Coalesce(Sum("amount"), Value(Decimal("0.00"))))["total"]

        return credit_sum - debit_sum

    @staticmethod
    def trainer_available_for_payout(trainer) -> Decimal:
        allocated = PayoutItem.objects.filter(
            ledger_entry__trainer=trainer,
            status__in=["allocated", "paid"],
        ).aggregate(total=Coalesce(Sum("amount"), Value(Decimal("0.00"))))["total"]
        return TrainerBalanceSelector.trainer_payable_balance(trainer) - allocated

    @staticmethod
    def payout_candidates_queryset(trainer):
        allocated_ids = PayoutItem.objects.values_list("ledger_entry_id", flat=True)
        return LedgerEntry.objects.filter(
            trainer=trainer,
            account=LedgerAccount.TRAINER_PAYABLE,
            direction=LedgerDirection.CREDIT,
        ).exclude(id__in=allocated_ids)
