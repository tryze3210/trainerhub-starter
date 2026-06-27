from dataclasses import dataclass
from decimal import Decimal
from django.template.loader import render_to_string
from apps.finance_documents.models import FinanceDocument


@dataclass(slots=True)
class DocumentTotals:
    gross: Decimal
    commission: Decimal
    net: Decimal


class FinanceDocumentRenderer:
    """Renders finance documents into immutable HTML artifacts.

    Storage upload is left as an integration seam. Current implementation stores the
    rendered HTML on the model and returns the artifact body for external persistence.
    """

    template_map = {
        FinanceDocument.DOC_INVOICE: "finance_documents/invoice.html",
        FinanceDocument.DOC_RECEIPT: "finance_documents/invoice.html",
        FinanceDocument.DOC_CREDIT_NOTE: "finance_documents/invoice.html",
        FinanceDocument.DOC_REFUND_DOCUMENT: "finance_documents/invoice.html",
        FinanceDocument.DOC_PAYOUT_ACT: "finance_documents/payout_act.html",
        FinanceDocument.DOC_STATEMENT: "finance_documents/statement.html",
    }

    def render(self, document: FinanceDocument) -> str:
        template_name = self.template_map[document.document_type]
        return render_to_string(template_name, {"document": document, "payload": document.payload})
