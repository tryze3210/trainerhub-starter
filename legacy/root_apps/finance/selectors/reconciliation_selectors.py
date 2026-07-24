from apps.finance.models import ReconciliationDiscrepancy, ReconciliationSession, SettlementTransaction


class FinanceReconciliationSelector:
    @staticmethod
    def sessions():
        return ReconciliationSession.objects.order_by("-created_at")

    @staticmethod
    def discrepancies(*, status=None):
        qs = ReconciliationDiscrepancy.objects.select_related("session", "settlement_transaction").order_by("-created_at")
        if status:
            qs = qs.filter(status=status)
        return qs

    @staticmethod
    def settlement_transactions(*, provider=None, status=None):
        qs = SettlementTransaction.objects.select_related("payout_batch", "payout_item", "trainer").order_by("-created_at")
        if provider:
            qs = qs.filter(provider=provider)
        if status:
            qs = qs.filter(status=status)
        return qs
