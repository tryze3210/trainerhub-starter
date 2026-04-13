from dataclasses import dataclass
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.finance_documents.models import FinanceDocument

User = get_user_model()


@dataclass(slots=True)
class BuildContext:
    trainer: User
    period_start: object
    period_end: object
    gross_amount: Decimal
    commission_amount: Decimal
    net_amount: Decimal
    payload: dict


class FinanceDocumentBuilder:
    """Builds immutable document rows from existing finance_reporting slices.

    Replace the stubbed aggregation with your real v34 settlement sources.
    """

    def _number(self, doc_type: str, trainer_id: int) -> str:
        stamp = timezone.now().strftime("%Y%m%d%H%M%S")
        return f"{doc_type.upper()}-{trainer_id}-{stamp}"

    def build(self, *, doc_type: str, context: BuildContext) -> FinanceDocument:
        return FinanceDocument.objects.create(
            trainer=context.trainer,
            document_type=doc_type,
            period_start=context.period_start,
            period_end=context.period_end,
            document_number=self._number(doc_type, context.trainer.id),
            gross_amount=context.gross_amount,
            commission_amount=context.commission_amount,
            net_amount=context.net_amount,
            payload=context.payload,
        )
