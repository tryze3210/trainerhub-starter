from django.db import transaction
from django.utils import timezone

from apps.moderation.domain.models import (
    ModerationCase,
    ModerationCaseEvent,
    ModerationDecision,
    ModerationReviewDecision,
    ModerationStatus,
)


class ModerationCaseService:
    @transaction.atomic
    def create_case(self, *, target_type: str, target_id: str, title: str, summary: str = "", trainer=None, queue: str = "default", priority: int = 50):
        case = ModerationCase.objects.create(
            target_type=target_type,
            target_id=str(target_id),
            title=title,
            summary=summary,
            trainer=trainer,
            queue=queue,
            priority=priority,
        )
        ModerationCaseEvent.objects.create(case=case, event_type="case_opened", payload={"queue": queue, "priority": priority})
        return case

    @transaction.atomic
    def assign_case(self, *, case: ModerationCase, actor, assignee):
        case.assigned_to = assignee
        case.status = ModerationStatus.IN_REVIEW
        case.save(update_fields=["assigned_to", "status", "updated_at"])
        ModerationCaseEvent.objects.create(case=case, actor=actor, event_type="case_assigned", payload={"assignee_id": getattr(assignee, "id", None)})
        return case

    @transaction.atomic
    def submit_decision(self, *, case: ModerationCase, reviewer, decision: str, reason: str = "", metadata=None):
        metadata = metadata or {}
        ModerationReviewDecision.objects.create(
            case=case,
            reviewer=reviewer,
            decision=decision,
            reason=reason,
            metadata=metadata,
        )
        case.latest_decision = decision
        case.status = ModerationStatus.RESOLVED if decision in {ModerationDecision.APPROVED, ModerationDecision.REJECTED, ModerationDecision.NEEDS_CHANGES} else ModerationStatus.ESCALATED
        if case.status == ModerationStatus.RESOLVED:
            case.resolved_at = timezone.now()
        case.save(update_fields=["latest_decision", "status", "resolved_at", "updated_at"])
        ModerationCaseEvent.objects.create(case=case, actor=reviewer, event_type="decision_submitted", payload={"decision": decision, "metadata": metadata})
        return case
