from celery import shared_task

from apps.finance_reporting.services.reconciliation import FinanceReconciliationService


@shared_task
def refresh_finance_reconciliation_snapshots(days=30):
    FinanceReconciliationService().bootstrap_recent_snapshots(days=days)


@shared_task
def build_settlement_report(period_start, period_end):
    FinanceReconciliationService().build_settlement_report(period_start=period_start, period_end=period_end)
