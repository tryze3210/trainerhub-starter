from __future__ import annotations

from dataclasses import dataclass
from django.utils import timezone

from apps.disputes.models import DisputeCase, DisputeEvent, RefundReview, ChargebackOperation, SupportInboxItem


@dataclass
class CreateDisputeCaseDTO:
    opened_by_id: int
    dispute_type: str
    subject: str
    summary: str = ""
    reason_code: str = ""
    trainer_id: str | None = None
    order_id: str | None = None
    payment_id: str | None = None


class DisputeCaseService:
    @staticmethod
    def _generate_public_id() -> str:
        return timezone.now().strftime("DSP%Y%m%d%H%M%S%f")

    @classmethod
    def create_case(cls, dto: CreateDisputeCaseDTO) -> DisputeCase:
        case = DisputeCase.objects.create(
            public_id=cls._generate_public_id(),
            opened_by_id=dto.opened_by_id,
            dispute_type=dto.dispute_type,
            subject=dto.subject,
            summary=dto.summary,
            reason_code=dto.reason_code,
            trainer_id=dto.trainer_id,
            order_id=dto.order_id,
            payment_id=dto.payment_id,
        )
        DisputeEvent.objects.create(dispute_case=case, actor_id=dto.opened_by_id, event_type=DisputeEvent.EVENT_CREATED, body=dto.summary)
        if dto.dispute_type == DisputeCase.TYPE_REFUND:
            RefundReview.objects.create(dispute_case=case)
        if dto.dispute_type == DisputeCase.TYPE_CHARGEBACK:
            ChargebackOperation.objects.create(dispute_case=case)
        SupportInboxItem.objects.create(dispute_case=case)
        return case

    @staticmethod
    def set_status(case: DisputeCase, *, actor_id: int | None, status: str, note: str = "") -> DisputeCase:
        case.status = status
        if status in {DisputeCase.STATUS_RESOLVED, DisputeCase.STATUS_REJECTED}:
            case.resolved_at = timezone.now()
        case.save(update_fields=["status", "resolved_at", "updated_at"])
        DisputeEvent.objects.create(
            dispute_case=case,
            actor_id=actor_id,
            event_type=DisputeEvent.EVENT_STATUS_CHANGED,
            body=note,
            payload={"status": status},
        )
        return case
