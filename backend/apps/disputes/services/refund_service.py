from django.utils import timezone

from apps.disputes.models import DisputeEvent, RefundReview


class RefundReviewService:
    @staticmethod
    def review(refund_review: RefundReview, *, reviewed_by_id: int, decision: str, approved_amount, rationale: str = "") -> RefundReview:
        refund_review.decision = decision
        refund_review.approved_amount = approved_amount
        refund_review.reviewed_by_id = reviewed_by_id
        refund_review.reviewed_at = timezone.now()
        refund_review.rationale = rationale
        refund_review.save()
        DisputeEvent.objects.create(
            dispute_case=refund_review.dispute_case,
            actor_id=reviewed_by_id,
            event_type=DisputeEvent.EVENT_REFUND_REVIEWED,
            body=rationale,
            payload={"decision": decision, "approved_amount": str(approved_amount)},
        )
        return refund_review
