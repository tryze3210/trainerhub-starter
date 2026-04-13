from django.db import transaction
from django.utils import timezone

from finance_closing.constants import ClosingPeriodStatus
from finance_closing.models import ClosingGuardFailure, ClosingPeriod, FinanceCloseAuditLog
from finance_closing.selectors.periods import get_period_finance_summary
from finance_closing.selectors.statements import list_trainer_statements_for_period
from finance_closing.services.snapshot_service import SnapshotService
from finance_closing.services.statement_service import TrainerStatementService
from payouts.models import PayoutBatch
from reconciliation.models import ReconciliationDiscrepancy


class FinanceClosingService:
    @classmethod
    def assert_close_guards(cls, *, period: ClosingPeriod):
        unresolved_discrepancies = ReconciliationDiscrepancy.objects.filter(status__in=['open', 'investigating'])
        if unresolved_discrepancies.exists():
            raise ClosingGuardFailure('Unresolved reconciliation discrepancies exist.')

        open_batches = PayoutBatch.objects.filter(status__in=['draft', 'processing'])
        if open_batches.exists():
            raise ClosingGuardFailure('Open payout batches exist.')

    @classmethod
    @transaction.atomic
    def close_period(cls, *, period: ClosingPeriod, actor=None):
        cls.assert_close_guards(period=period)
        period.status = ClosingPeriodStatus.CLOSING
        period.save(update_fields=['status', 'updated_at'])
        FinanceCloseAuditLog.objects.create(period=period, actor=actor, action='period_closing_started')

        snapshot = SnapshotService.generate_month_end_snapshot(period=period, actor=actor)

        trainers = set(
            item['trainer_id']
            for item in snapshot.payload.get('trainer_summaries', [])
        )
        if not trainers:
            from trainers.models import Trainer
            trainers = set(Trainer.objects.filter(status='active').values_list('id', flat=True))

        from trainers.models import Trainer
        for trainer in Trainer.objects.filter(id__in=trainers):
            statement = TrainerStatementService.build_or_replace_statement(trainer=trainer, period=period, snapshot=snapshot)
            TrainerStatementService.issue_statement_document(statement=statement)

        period.status = ClosingPeriodStatus.CLOSED
        period.closed_at = timezone.now()
        period.closed_by = actor
        period.save(update_fields=['status', 'closed_at', 'closed_by', 'updated_at'])
        FinanceCloseAuditLog.objects.create(
            period=period,
            actor=actor,
            action='period_closed',
            details=get_period_finance_summary(period),
        )
        return period

    @classmethod
    @transaction.atomic
    def reopen_period(cls, *, period: ClosingPeriod, actor=None, reason: str = ''):
        period.status = ClosingPeriodStatus.REOPENED
        period.closed_at = None
        period.closed_by = None
        period.save(update_fields=['status', 'closed_at', 'closed_by', 'updated_at'])
        FinanceCloseAuditLog.objects.create(
            period=period,
            actor=actor,
            action='period_reopened',
            details={'reason': reason},
        )
        return period
