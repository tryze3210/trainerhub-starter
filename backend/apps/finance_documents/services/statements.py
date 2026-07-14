from decimal import Decimal
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django.contrib.auth import get_user_model
from apps.finance_documents.services.builders import BuildContext, FinanceDocumentBuilder
from apps.finance_documents.models import FinanceDocument
from apps.payments.services import PaymentService
from apps.payouts.models import BalanceEntry

User = get_user_model()


class TrainerStatementService:
    def __init__(self) -> None:
        self.builder = FinanceDocumentBuilder()

    @staticmethod
    def _money(value) -> Decimal:
        return Decimal(str(value or "0.00")).quantize(Decimal("0.01"))

    @classmethod
    def _sum_amount(cls, queryset) -> Decimal:
        return cls._money(queryset.aggregate(total=Coalesce(Sum("amount"), Decimal("0.00")))["total"])

    @classmethod
    def _gross_from_net(cls, net_amount: Decimal) -> Decimal:
        payout_ratio = Decimal("1.00") - PaymentService.PLATFORM_FEE_RATE
        if payout_ratio <= Decimal("0.00"):
            return net_amount
        return (net_amount / payout_ratio).quantize(Decimal("0.01"))

    def build_monthly_statement(self, *, trainer: User, period_start, period_end) -> FinanceDocument:
        entries = BalanceEntry.objects.filter(
            wallet__trainer__user=trainer,
            created_at__date__gte=period_start,
            created_at__date__lte=period_end,
        )
        accruals = entries.filter(entry_type=BalanceEntry.EntryType.ACCRUAL, direction="credit")
        reversals = entries.filter(entry_type=BalanceEntry.EntryType.REVERSAL, direction="debit")
        payouts = entries.filter(entry_type=BalanceEntry.EntryType.PAYOUT, direction="debit")
        reserves = entries.filter(entry_type=BalanceEntry.EntryType.RESERVE, direction="debit")
        releases = entries.filter(entry_type=BalanceEntry.EntryType.RELEASE, direction="credit")
        risk_holds = entries.filter(entry_type=BalanceEntry.EntryType.RISK_HOLD, direction="debit")

        accrual_net = self._sum_amount(accruals)
        reversal_net = self._sum_amount(reversals)
        net = max(accrual_net - reversal_net, Decimal("0.00")).quantize(Decimal("0.01"))
        gross = self._gross_from_net(net)
        commission = (gross - net).quantize(Decimal("0.01"))

        payload = {
            "summary": {
                "orders_count": accruals.values("source_id").distinct().count(),
                "refunds_count": reversals.count(),
                "payouts_count": payouts.count(),
            },
            "ledger": {
                "accrual_net_amount": str(accrual_net),
                "reversal_net_amount": str(reversal_net),
                "payout_paid_amount": str(self._sum_amount(payouts)),
                "payout_reserved_amount": str(self._sum_amount(reserves)),
                "payout_released_amount": str(self._sum_amount(releases)),
                "risk_hold_amount": str(self._sum_amount(risk_holds)),
                "entries_count": entries.aggregate(total=Coalesce(Count("id"), 0))["total"],
            },
            "source": "payout_ledger",
        }
        return self.builder.build(
            doc_type=FinanceDocument.DOC_STATEMENT,
            context=BuildContext(
                trainer=trainer,
                period_start=period_start,
                period_end=period_end,
                gross_amount=gross,
                commission_amount=commission,
                net_amount=net,
                payload=payload,
            ),
        )
