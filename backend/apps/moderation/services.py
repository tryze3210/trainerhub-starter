from __future__ import annotations

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.audit.services import AuditService

from apps.moderation.models import (
    ModerationCase,
    ModerationCaseEvent,
    ModerationDecision,
    ModerationReviewDecision,
    ModerationStatus,
    TrainerRiskFlag,
)

try:
    from apps.trainer_cms.models import PublishStatus, TrainerVideoDraft
    from apps.trainer_cms.services import TrainerCMSService
except Exception:  # pragma: no cover
    PublishStatus = None
    TrainerVideoDraft = None
    TrainerCMSService = None


TERMINAL_DECISIONS = {
    ModerationDecision.APPROVED,
    ModerationDecision.REJECTED,
    ModerationDecision.NEEDS_CHANGES,
}


def normalize_moderation_decision(decision: str) -> str:
    return {
        "approve": ModerationDecision.APPROVED,
        "approved": ModerationDecision.APPROVED,
        "reject": ModerationDecision.REJECTED,
        "rejected": ModerationDecision.REJECTED,
        "request_changes": ModerationDecision.NEEDS_CHANGES,
        "changes_requested": ModerationDecision.NEEDS_CHANGES,
        "needs_changes": ModerationDecision.NEEDS_CHANGES,
        "escalate": ModerationDecision.ESCALATED,
        "escalated": ModerationDecision.ESCALATED,
    }.get(decision, decision)


class ModerationCaseService:
    """Admin moderation workflow service."""

    @transaction.atomic
    def assign_case(self, *, case: ModerationCase, actor, assignee):
        if case.status == ModerationStatus.RESOLVED and case.latest_decision in TERMINAL_DECISIONS:
            raise ValidationError({"detail": "Resolved moderation case cannot be reassigned."})

        case.assigned_to = assignee
        case.status = ModerationStatus.IN_REVIEW
        case.save(update_fields=["assigned_to", "status", "updated_at"])
        ModerationCaseEvent.objects.create(
            case=case,
            actor=actor,
            event_type="assigned",
            payload={"assignee_id": str(assignee.id)},
        )
        AuditService.log(
            actor=actor,
            event_type="moderation.assigned",
            entity_type="moderation_case",
            entity_id=str(case.id),
            context={"assignee_id": str(assignee.id), "queue": case.queue},
        )
        return case

    @transaction.atomic
    def submit_decision(self, *, case: ModerationCase, reviewer, decision: str, reason: str = "", metadata: dict | None = None):
        decision = normalize_moderation_decision(decision)
        metadata = metadata or {}

        if case.status == ModerationStatus.RESOLVED and case.latest_decision in TERMINAL_DECISIONS:
            raise ValidationError({"detail": "Moderation case is already resolved.", "latest_decision": case.latest_decision})

        ModerationReviewDecision.objects.create(
            case=case,
            reviewer=reviewer,
            decision=decision,
            reason=reason,
            metadata=metadata,
        )

        case.latest_decision = decision
        if decision == ModerationDecision.ESCALATED:
            case.status = ModerationStatus.ESCALATED
            case.resolved_at = None
        else:
            case.status = ModerationStatus.RESOLVED
            case.resolved_at = timezone.now()

        case.save(update_fields=["latest_decision", "status", "resolved_at", "updated_at"])
        ModerationCaseEvent.objects.create(
            case=case,
            actor=reviewer,
            event_type="decision_submitted",
            payload={"decision": decision, "reason": reason, "metadata": metadata},
        )
        AuditService.log(
            actor=reviewer,
            event_type="moderation.decision",
            entity_type="moderation_case",
            entity_id=str(case.id),
            context={"decision": decision, "reason": reason, "queue": case.queue, "target_type": case.target_type, "target_id": case.target_id},
        )

        self._propagate_trainer_onboarding_decision(case=case, decision=decision, reason=reason)
        return case

    def _propagate_trainer_onboarding_decision(self, *, case: ModerationCase, decision: str, reason: str):
        if case.queue != "trainer_onboarding":
            return None

        from apps.trainers.models import TrainerApplication
        from apps.trainers.services.applications import TrainerApplicationService

        application = TrainerApplication.objects.filter(id=case.target_id).select_related("user").first()
        if application is None:
            ModerationCaseEvent.objects.create(
                case=case,
                actor=None,
                event_type="target_missing",
                payload={"target_type": case.target_type, "target_id": case.target_id},
            )
            return None

        return TrainerApplicationService().apply_moderation_decision(
            application=application,
            decision=decision,
            reviewer_note=reason,
        )


class TrainerRiskService:
    """Risk flag operations for marketplace admin moderation."""

    @transaction.atomic
    def raise_flag(self, *, trainer, code: str, label: str, risk_level: str, source: str = "manual", details: dict | None = None):
        flag = TrainerRiskFlag.objects.create(
            trainer=trainer,
            code=code,
            label=label,
            risk_level=risk_level,
            source=source,
            details=details or {},
        )
        AuditService.log(
            event_type="risk_flag.created",
            entity_type="trainer_risk_flag",
            entity_id=str(flag.id),
            context={"trainer_id": str(trainer.id), "code": code, "risk_level": risk_level, "source": source},
        )
        return flag

    @transaction.atomic
    def resolve_flag(self, *, flag: TrainerRiskFlag):
        flag.is_active = False
        flag.resolved_at = timezone.now()
        flag.save(update_fields=["is_active", "resolved_at"])
        AuditService.log(
            event_type="risk_flag.resolved",
            entity_type="trainer_risk_flag",
            entity_id=str(flag.id),
            context={"trainer_id": str(flag.trainer_id), "code": flag.code, "risk_level": flag.risk_level},
        )
        return flag


class ModerationService:
    """Compatibility service for the older trainer CMS video moderation flow."""

    def __init__(self):
        self.cms_service = TrainerCMSService() if TrainerCMSService else None

    @transaction.atomic
    def approve_video(self, moderation_case: ModerationCase, *, actor_id, comment: str = ""):
        ModerationReviewDecision.objects.create(
            case=moderation_case,
            reviewer_id=actor_id,
            decision=ModerationDecision.APPROVED,
            reason=comment,
        )
        moderation_case.status = ModerationStatus.RESOLVED
        moderation_case.latest_decision = ModerationDecision.APPROVED
        moderation_case.resolved_at = timezone.now()
        moderation_case.save(update_fields=["status", "latest_decision", "resolved_at", "updated_at"])

        if TrainerVideoDraft is not None and self.cms_service is not None:
            draft = TrainerVideoDraft.objects.get(id=moderation_case.target_id)
            self.cms_service.publish_video(draft, actor_id=actor_id)
        return moderation_case

    @transaction.atomic
    def reject_video(self, moderation_case: ModerationCase, *, actor_id, comment: str):
        ModerationReviewDecision.objects.create(
            case=moderation_case,
            reviewer_id=actor_id,
            decision=ModerationDecision.REJECTED,
            reason=comment,
        )
        moderation_case.status = ModerationStatus.RESOLVED
        moderation_case.latest_decision = ModerationDecision.REJECTED
        moderation_case.resolved_at = timezone.now()
        moderation_case.save(update_fields=["status", "latest_decision", "resolved_at", "updated_at"])

        if TrainerVideoDraft is not None and PublishStatus is not None:
            TrainerVideoDraft.objects.filter(id=moderation_case.target_id).update(status=PublishStatus.DRAFT)
        return moderation_case
