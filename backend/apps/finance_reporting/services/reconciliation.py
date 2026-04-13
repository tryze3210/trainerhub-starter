from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.apps import apps
from django.db.models import Count, Max, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.finance_reporting.models import (
    FinanceReconciliationSnapshot,
    SettlementReport,
    TrainerSettlementLine,
)


class FinanceReconciliationService:
    """
    Central integration seam for finance reporting.
    Adapt app labels / field names here if your domain models differ.
    """

    def _get_models(self):
        Order = apps.get_model("orders", "Order")
        Payment = apps.get_model("payments", "Payment")
        Payout = apps.get_model("payments", "Payout")
        return Order, Payment, Payout

    def refresh_snapshot(self, snapshot_date=None):
        snapshot_date = snapshot_date or timezone.localdate()
        Order, Payment, Payout = self._get_models()

        orders = Order.objects.filter(created_at__date__lte=snapshot_date)
        payments = Payment.objects.filter(created_at__date__lte=snapshot_date)
        payouts = Payout.objects.filter(created_at__date__lte=snapshot_date)

        gross_sales_amount = orders.aggregate(v=Coalesce(Sum("total_amount"), Decimal("0")))["v"]
        successful_payment_amount = payments.filter(status="succeeded").aggregate(v=Coalesce(Sum("amount"), Decimal("0")))["v"]
        refunded_amount = payments.filter(status="refunded").aggregate(v=Coalesce(Sum("amount"), Decimal("0")))["v"]
        trainer_payout_amount = payouts.filter(status="paid").aggregate(v=Coalesce(Sum("amount"), Decimal("0")))["v"]
        recognized_commission_amount = gross_sales_amount - trainer_payout_amount - refunded_amount
        settlement_gap_amount = successful_payment_amount - trainer_payout_amount - refunded_amount - recognized_commission_amount
        unmatched_payment_count = payments.filter(order__isnull=True).count()
        unmatched_payout_count = payouts.filter(order__isnull=True).count()

        snapshot, _ = FinanceReconciliationSnapshot.objects.update_or_create(
            snapshot_date=snapshot_date,
            defaults={
                "gross_sales_amount": gross_sales_amount,
                "successful_payment_amount": successful_payment_amount,
                "refunded_amount": refunded_amount,
                "trainer_payout_amount": trainer_payout_amount,
                "recognized_commission_amount": recognized_commission_amount,
                "settlement_gap_amount": settlement_gap_amount,
                "unmatched_payment_count": unmatched_payment_count,
                "unmatched_payout_count": unmatched_payout_count,
            },
        )
        return snapshot

    def build_settlement_report(self, period_start, period_end):
        Order, Payment, Payout = self._get_models()
        report, _ = SettlementReport.objects.get_or_create(period_start=period_start, period_end=period_end)
        report.lines.all().delete()

        trainer_rows = (
            Order.objects.filter(created_at__date__gte=period_start, created_at__date__lte=period_end, status="paid")
            .values("trainer_id")
            .annotate(
                gross_amount=Coalesce(Sum("total_amount"), Decimal("0")),
                order_count=Count("id"),
                last_order_at=Max("created_at"),
            )
        )

        for row in trainer_rows:
            trainer_id = row["trainer_id"]
            refund_amount = Payment.objects.filter(order__trainer_id=trainer_id, status="refunded", created_at__date__gte=period_start, created_at__date__lte=period_end).aggregate(v=Coalesce(Sum("amount"), Decimal("0")))["v"]
            refund_count = Payment.objects.filter(order__trainer_id=trainer_id, status="refunded", created_at__date__gte=period_start, created_at__date__lte=period_end).count()
            paid_amount = Payout.objects.filter(order__trainer_id=trainer_id, status="paid", created_at__date__gte=period_start, created_at__date__lte=period_end).aggregate(v=Coalesce(Sum("amount"), Decimal("0")))["v"]
            payout_count = Payout.objects.filter(order__trainer_id=trainer_id, created_at__date__gte=period_start, created_at__date__lte=period_end).count()
            commission_amount = (row["gross_amount"] * Decimal("0.20")).quantize(Decimal("0.01"))
            payout_amount = row["gross_amount"] - refund_amount - commission_amount
            pending_amount = payout_amount - paid_amount

            TrainerSettlementLine.objects.create(
                report=report,
                trainer_id=trainer_id,
                gross_amount=row["gross_amount"],
                refund_amount=refund_amount,
                commission_amount=commission_amount,
                payout_amount=payout_amount,
                paid_amount=paid_amount,
                pending_amount=pending_amount,
                order_count=row["order_count"],
                refund_count=refund_count,
                payout_count=payout_count,
                last_order_at=row["last_order_at"],
            )

        self.refresh_snapshot(snapshot_date=period_end)
        return report

    def bootstrap_recent_snapshots(self, days=30):
        today = timezone.localdate()
        for i in range(days):
            self.refresh_snapshot(snapshot_date=today - timedelta(days=i))
