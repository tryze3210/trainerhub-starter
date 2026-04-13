"""Integration seams for v39.

Wire these functions from payment/refund/chargeback application services,
not from views and not from model save() hooks.
"""

from apps.disputes.services.case_service import CreateDisputeCaseDTO, DisputeCaseService
from apps.disputes.models import DisputeCase


def open_refund_case(*, user_id, order_id, payment_id, trainer_id, subject, summary, reason_code="refund_request"):
    return DisputeCaseService.create_case(
        CreateDisputeCaseDTO(
            opened_by_id=user_id,
            dispute_type=DisputeCase.TYPE_REFUND,
            subject=subject,
            summary=summary,
            reason_code=reason_code,
            trainer_id=trainer_id,
            order_id=order_id,
            payment_id=payment_id,
        )
    )


def open_chargeback_case(*, user_id, payment_id, trainer_id, provider_case_id, amount, currency):
    case = DisputeCaseService.create_case(
        CreateDisputeCaseDTO(
            opened_by_id=user_id,
            dispute_type=DisputeCase.TYPE_CHARGEBACK,
            subject="Chargeback opened",
            summary=f"Provider case {provider_case_id}",
            reason_code="unauthorized_payment",
            trainer_id=trainer_id,
            payment_id=payment_id,
        )
    )
    chargeback = case.chargeback_operation
    chargeback.provider_case_id = provider_case_id
    chargeback.amount = amount
    chargeback.currency = currency
    chargeback.save()
    return case
