from finance_closing.models import TrainerMonthStatement


def get_trainer_statement(*, trainer, period):
    return (
        TrainerMonthStatement.objects
        .select_related('trainer', 'period', 'snapshot', 'accounting_document')
        .filter(trainer=trainer, period=period)
        .first()
    )


def list_trainer_statements_for_period(*, period):
    return (
        TrainerMonthStatement.objects
        .select_related('trainer', 'accounting_document')
        .filter(period=period)
        .order_by('trainer_id')
    )
