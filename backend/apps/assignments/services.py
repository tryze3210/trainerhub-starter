from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.assignments.models import (
    Assignment,
    AssignmentContentType,
    AssignmentStatus,
    AssignmentSubmission,
    SubmissionStatus,
)
from apps.access_control.permissions import ROLE_ADMIN, ROLE_TRAINER, user_role_set
from apps.entitlements.access_audit import AccessControlAuditService


def _is_trainer(user) -> bool:
    roles = user_role_set(user)
    return bool(roles.intersection({ROLE_TRAINER, ROLE_ADMIN}) or getattr(user, "is_staff", False))


def _can_review(user, assignment: Assignment) -> bool:
    return bool(getattr(user, "is_staff", False) or assignment.trainer_id == getattr(user, "id", None))


def _access_decision(*, user, assignment: Assignment) -> dict[str, Any]:
    return AccessControlAuditService.check(
        user=user,
        target_type=assignment.content_type,
        target_id=assignment.content_id,
        include_admin_override=False,
    )


def _validate_assignment_target_ownership(*, trainer, content_type: str, content_id: str) -> None:
    target_model = None
    target_label = ""
    if content_type == AssignmentContentType.COURSE:
        from apps.trainer_cms.models import TrainerCourseDraft as target_model

        target_label = "Course"
    elif content_type == AssignmentContentType.PROGRAM:
        from apps.trainer_cms.models import TrainerProgramDraft as target_model

        target_label = "Program"
    if target_model is None:
        return

    try:
        target = target_model.objects.filter(id=content_id).first()
    except ValidationError:
        target = None
    if target is None:
        raise ValidationError({"content_id": f"{target_label} not found."})
    if str(target.trainer_id) != str(getattr(trainer, "id", "") or "") and not getattr(trainer, "is_staff", False):
        raise PermissionDenied(f"Only the content owner can create assignments for this {target_label.lower()}.")


class AssignmentService:
    @staticmethod
    def create_assignment(*, trainer, data: dict[str, Any]) -> Assignment:
        if not _is_trainer(trainer):
            raise PermissionDenied("Trainer role required.")
        content_type = data.get("content_type")
        if content_type not in AssignmentContentType.values:
            raise ValidationError({"content_type": "Unsupported assignment content type."})
        content_id = str(data.get("content_id", "")).strip()
        _validate_assignment_target_ownership(trainer=trainer, content_type=content_type, content_id=content_id)
        return Assignment.objects.create(
            trainer=trainer,
            title=data.get("title", "").strip(),
            description=data.get("description", "").strip(),
            content_type=content_type,
            content_id=content_id,
            lesson_id=str(data.get("lesson_id", "")).strip(),
            due_at=data.get("due_at"),
            status=data.get("status") or AssignmentStatus.PUBLISHED,
            metadata=data.get("metadata") or {},
        )

    @staticmethod
    @transaction.atomic
    def submit_assignment(*, student, assignment: Assignment, data: dict[str, Any]) -> AssignmentSubmission:
        if assignment.status != AssignmentStatus.PUBLISHED:
            raise PermissionDenied("Assignment is not published.")
        decision = _access_decision(user=student, assignment=assignment)
        if not decision.get("allowed"):
            raise PermissionDenied("Active entitlement required for this assignment.")
        submission, _created = AssignmentSubmission.objects.select_for_update().get_or_create(
            assignment=assignment,
            student=student,
            defaults={"submitted_at": timezone.now()},
        )
        submission.answer_text = data.get("answer_text", "").strip()
        submission.attachments = data.get("attachments") or []
        submission.status = SubmissionStatus.SUBMITTED
        submission.submitted_at = timezone.now()
        submission.reviewed_at = None
        submission.reviewed_by = None
        submission.review_comment = ""
        submission.score = None
        submission.save(
            update_fields=[
                "answer_text",
                "attachments",
                "status",
                "submitted_at",
                "reviewed_at",
                "reviewed_by",
                "review_comment",
                "score",
                "updated_at",
            ]
        )
        return submission

    @staticmethod
    @transaction.atomic
    def review_submission(*, trainer, submission: AssignmentSubmission, data: dict[str, Any]) -> AssignmentSubmission:
        assignment = Assignment.objects.select_for_update().get(pk=submission.assignment_id)
        if not _can_review(trainer, assignment):
            raise PermissionDenied("Only assignment trainer can review this submission.")
        status = data.get("status") or SubmissionStatus.REVIEWED
        if status not in {SubmissionStatus.REVIEWED, SubmissionStatus.NEEDS_REVISION, SubmissionStatus.APPROVED}:
            raise ValidationError({"status": "Unsupported review status."})
        submission.status = status
        submission.review_comment = data.get("review_comment", "").strip()
        submission.score = data.get("score")
        submission.reviewed_by = trainer
        submission.reviewed_at = timezone.now()
        submission.save(
            update_fields=["status", "review_comment", "score", "reviewed_by", "reviewed_at", "updated_at"]
        )
        return submission
