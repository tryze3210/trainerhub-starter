from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from decimal import Decimal
from io import StringIO
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.audit.services import AuditService
from apps.finance_documents.models import FinanceDocument
from apps.finance_documents.services.rendering import FinanceDocumentRenderer
from apps.orders.models import Order
from apps.payments.models import Payment


@dataclass(slots=True)
class BuildFinanceDocumentResult:
    document: FinanceDocument
    created: bool


class FinanceCommercialDocumentService:
    ACCOUNTANT_EXPORT_FIELDS = [
        "document_number",
        "document_type",
        "status",
        "owner_id",
        "owner_email",
        "period_start",
        "period_end",
        "currency",
        "gross_amount",
        "commission_amount",
        "net_amount",
        "order_id",
        "payment_id",
        "refund_id",
        "provider",
        "created_at",
        "finalized_at",
    ]

    @staticmethod
    def _money(value) -> Decimal:
        return Decimal(str(value or "0.00")).quantize(Decimal("0.01"))

    @staticmethod
    def _document_prefix(document_type: str) -> str:
        return {
            FinanceDocument.DOC_INVOICE: "INV",
            FinanceDocument.DOC_RECEIPT: "RCPT",
            FinanceDocument.DOC_CREDIT_NOTE: "CRN",
            FinanceDocument.DOC_REFUND_DOCUMENT: "RFD",
            FinanceDocument.DOC_PAYOUT_ACT: "PACT",
            FinanceDocument.DOC_STATEMENT: "STMT",
        }.get(document_type, "FDOC")

    @classmethod
    def _document_number(cls, *, document_type: str, source_id: str) -> str:
        prefix = cls._document_prefix(document_type)
        normalized = str(source_id).replace(" ", "-")
        if len(normalized) > 48:
            normalized = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:24]
        return f"{prefix}-{normalized}"

    @staticmethod
    def _legal_payload(user) -> dict[str, Any]:
        kyc = getattr(user, "trainer_kyc_profile", None)
        finance_profile = getattr(user, "finance_profile", None)
        return {
            "legal_name": (
                getattr(kyc, "payout_legal_entity_name", "")
                or getattr(finance_profile, "legal_name", "")
                or getattr(user, "email", "")
            ),
            "tax_id": getattr(kyc, "tax_id", "") or getattr(finance_profile, "tax_number", ""),
            "legal_address": getattr(kyc, "legal_address", ""),
            "country": getattr(kyc, "country", ""),
        }

    @staticmethod
    def _order_payload(*, order: Order, payment: Payment | None = None, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        items = [
            {
                "id": str(item.id),
                "item_type": item.item_type,
                "item_id": str(item.item_id),
                "title": item.title_snapshot,
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "total_price": str(item.total_price),
                "metadata": item.metadata or {},
            }
            for item in order.items.order_by("created_at")
        ]
        return {
            "order_id": str(order.id),
            "payment_id": str(payment.id) if payment else "",
            "provider": payment.provider if payment else "",
            "external_payment_id": payment.external_payment_id if payment else "",
            "order_status": order.status,
            "payment_status": payment.status if payment else "",
            "buyer_legal": FinanceCommercialDocumentService._legal_payload(order.user),
            "items": items,
            **(extra or {}),
        }

    @classmethod
    def _render_and_save(cls, document: FinanceDocument) -> FinanceDocument:
        document.rendered_html = FinanceDocumentRenderer().render(document)
        document.save(update_fields=["rendered_html", "updated_at"])
        return document

    @classmethod
    @transaction.atomic
    def build_for_order(
        cls,
        *,
        document_type: str,
        order: Order,
        payment: Payment | None = None,
        actor=None,
        request=None,
    ) -> BuildFinanceDocumentResult:
        if document_type not in {FinanceDocument.DOC_INVOICE, FinanceDocument.DOC_RECEIPT}:
            raise ValueError("document_type must be invoice or receipt")
        source_id = f"{order.id}" if document_type == FinanceDocument.DOC_INVOICE else f"{order.id}-{payment.id if payment else 'nopayment'}"
        document_number = cls._document_number(document_type=document_type, source_id=source_id)
        gross_amount = cls._money(getattr(payment, "amount", None) or order.total_amount)
        document, created = FinanceDocument.objects.update_or_create(
            document_number=document_number,
            defaults={
                "trainer": order.user,
                "document_type": document_type,
                "period_start": order.created_at.date(),
                "period_end": (getattr(payment, "confirmed_at", None) or order.updated_at).date(),
                "currency": order.currency,
                "gross_amount": gross_amount,
                "commission_amount": Decimal("0.00"),
                "net_amount": gross_amount,
                "payload": cls._order_payload(order=order, payment=payment),
            },
        )
        cls._render_and_save(document)
        AuditService.log_admin_action(
            action=f"finance_document.{document_type}.built",
            target_type="finance_document",
            target_id=str(document.id),
            actor=actor,
            request=request,
            context={"order_id": str(order.id), "payment_id": str(getattr(payment, "id", "") or ""), "created": created},
        )
        return BuildFinanceDocumentResult(document=document, created=created)

    @classmethod
    @transaction.atomic
    def build_refund_document(
        cls,
        *,
        document_type: str,
        payment: Payment,
        refund_id: str,
        amount=None,
        reason: str = "",
        actor=None,
        request=None,
    ) -> BuildFinanceDocumentResult:
        if document_type not in {FinanceDocument.DOC_CREDIT_NOTE, FinanceDocument.DOC_REFUND_DOCUMENT}:
            raise ValueError("document_type must be credit_note or refund_document")
        order = payment.order
        refund_amount = cls._money(amount or payment.amount)
        document_number = cls._document_number(document_type=document_type, source_id=f"{payment.id}-{refund_id}")
        document, created = FinanceDocument.objects.update_or_create(
            document_number=document_number,
            defaults={
                "trainer": order.user,
                "document_type": document_type,
                "period_start": timezone.now().date(),
                "period_end": timezone.now().date(),
                "currency": payment.currency,
                "gross_amount": refund_amount,
                "commission_amount": Decimal("0.00"),
                "net_amount": refund_amount,
                "payload": cls._order_payload(
                    order=order,
                    payment=payment,
                    extra={"refund_id": refund_id, "refund_amount": str(refund_amount), "reason": reason},
                ),
            },
        )
        cls._render_and_save(document)
        AuditService.log_admin_action(
            action=f"finance_document.{document_type}.built",
            target_type="finance_document",
            target_id=str(document.id),
            actor=actor,
            request=request,
            reason=reason,
            context={"order_id": str(order.id), "payment_id": str(payment.id), "refund_id": refund_id, "created": created},
        )
        return BuildFinanceDocumentResult(document=document, created=created)

    @classmethod
    def export_for_accountant(cls, *, queryset) -> str:
        stream = StringIO()
        writer = csv.DictWriter(stream, fieldnames=cls.ACCOUNTANT_EXPORT_FIELDS)
        writer.writeheader()
        for document in queryset.select_related("trainer").order_by("created_at"):
            payload = document.payload or {}
            writer.writerow(
                {
                    "document_number": document.document_number,
                    "document_type": document.document_type,
                    "status": document.status,
                    "owner_id": str(document.trainer_id),
                    "owner_email": getattr(document.trainer, "email", ""),
                    "period_start": document.period_start.isoformat(),
                    "period_end": document.period_end.isoformat(),
                    "currency": document.currency,
                    "gross_amount": str(document.gross_amount),
                    "commission_amount": str(document.commission_amount),
                    "net_amount": str(document.net_amount),
                    "order_id": payload.get("order_id", ""),
                    "payment_id": payload.get("payment_id", ""),
                    "refund_id": payload.get("refund_id", ""),
                    "provider": payload.get("provider", ""),
                    "created_at": document.created_at.isoformat() if document.created_at else "",
                    "finalized_at": document.finalized_at.isoformat() if document.finalized_at else "",
                }
            )
        return stream.getvalue()
