from django.db.models import Count, Sum

from finance_closing.models import ClosingPeriod, FinanceSnapshot, TrainerMonthStatement


def list_closing_periods(*, status=None):
    qs = ClosingPeriod.objects.all().annotate(
        snapshot_count=Count('snapshots'),
        statement_count=Count('trainer_statements'),
    )
    if status:
        qs = qs.filter(status=status)
    return qs.order_by('-starts_at')



def get_period_finance_summary(period):
    statement_totals = TrainerMonthStatement.objects.filter(period=period).aggregate(
        gross_sales=Sum('gross_sales_amount'),
        refunds=Sum('refunds_amount'),
        commissions=Sum('commission_amount'),
        payout_fees=Sum('payout_fees_amount'),
        reserves=Sum('reserve_amount'),
        net_payable=Sum('net_payable_amount'),
    )
    latest_snapshot = FinanceSnapshot.objects.filter(period=period, status='ready').order_by('-version').first()
    return {
        'period_id': str(period.id),
        'period_code': period.code,
        'status': period.status,
        'statement_totals': statement_totals,
        'latest_snapshot_id': str(latest_snapshot.id) if latest_snapshot else None,
        'latest_snapshot_version': latest_snapshot.version if latest_snapshot else None,
    }
