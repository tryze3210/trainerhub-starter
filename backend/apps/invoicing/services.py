from apps.invoicing.models import Invoice


class InvoiceService:
    @staticmethod
    def build_number(*, document_type: str, order_id: str) -> str:
        prefix = 'RCPT' if document_type == Invoice.Type.RECEIPT else 'INV'
        return f'{prefix}-{order_id}'

    @classmethod
    def create_order_documents(cls, *, user, order, payment):
        invoice = Invoice.objects.create(
            user=user,
            order_id=str(order.id),
            payment_id=str(payment.id),
            document_type=Invoice.Type.INVOICE,
            document_number=cls.build_number(document_type=Invoice.Type.INVOICE, order_id=str(order.id)),
            currency=order.currency,
            gross_amount=order.gross_amount,
            payload={'title': order.title_snapshot, 'trainer_id': order.trainer_id},
        )
        receipt = Invoice.objects.create(
            user=user,
            order_id=str(order.id),
            payment_id=str(payment.id),
            document_type=Invoice.Type.RECEIPT,
            document_number=cls.build_number(document_type=Invoice.Type.RECEIPT, order_id=str(order.id)),
            currency=order.currency,
            gross_amount=order.gross_amount,
            payload={'title': order.title_snapshot, 'trainer_id': order.trainer_id},
        )
        return invoice, receipt
