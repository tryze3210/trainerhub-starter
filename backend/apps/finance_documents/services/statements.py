from decimal import Decimal
from django.contrib.auth import get_user_model
from apps.finance_documents.services.builders import BuildContext, FinanceDocumentBuilder
from apps.finance_documents.models import FinanceDocument

User = get_user_model()


class TrainerStatementService:
    def __init__(self) -> None:
        self.builder = FinanceDocumentBuilder()

    def build_monthly_statement(self, *, trainer: User, period_start, period_end) -> FinanceDocument:
        # Integration seam: replace with finance_reporting settlement snapshot lookup.
        gross = Decimal("10000.00")
        commission = Decimal("1500.00")
        net = gross - commission
        payload = {
            "summary": {
                "orders_count": 12,
                "refunds_count": 1,
                "payouts_count": 2,
            },
            "notes": "Replace stub metrics with v34 settlement report bindings.",
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
