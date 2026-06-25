from __future__ import annotations

from typing import Any

from django.db.models import Count, Q

from apps.assignments.models import Assignment, AssignmentStatus, AssignmentSubmission
from apps.entitlements.access_audit import AccessControlAuditService


def _iso(value: Any) -> str | None:
    return value.isoformat() if value else None


def _submission_payload(submission: AssignmentSubmission | None) -> dict[str, Any] | None:
    if submission is None:
        return None
    return {
        "id": str(submission.id),
        "assignment_id": str(submission.assignment_id),
        "student_id": str(submission.student_id),
        "student_email": getattr(submission.student, "email", ""),
        "answer_text": submission.answer_text,
        "attachments": submission.attachments or [],
        "status": submission.status,
        "submitted_at": _iso(submission.submitted_at),
        "reviewed_at": _iso(submission.reviewed_at),
        "reviewed_by_id": str(submission.reviewed_by_id) if submission.reviewed_by_id else None,
        "review_comment": submission.review_comment,
        "score": str(submission.score) if submission.score is not None else None,
        "created_at": _iso(submission.created_at),
        "updated_at": _iso(submission.updated_at),
    }


def assignment_payload(*, assignment: Assignment, submission: AssignmentSubmission | None = None) -> dict[str, Any]:
    return {
        "id": str(assignment.id),
        "trainer_id": str(assignment.trainer_id),
        "trainer_email": getattr(assignment.trainer, "email", ""),
        "title": assignment.title,
        "description": assignment.description,
        "content_type": assignment.content_type,
        "content_id": assignment.content_id,
        "lesson_id": assignment.lesson_id,
        "due_at": _iso(assignment.due_at),
        "status": assignment.status,
        "metadata": assignment.metadata or {},
        "created_at": _iso(assignment.created_at),
        "updated_at": _iso(assignment.updated_at),
        "submission": _submission_payload(submission),
    }


def list_student_assignments(*, user) -> dict[str, Any]:
    submissions = {
        str(item.assignment_id): item
        for item in AssignmentSubmission.objects.filter(student=user)
        .select_related("student", "reviewed_by", "assignment")
        .order_by("-submitted_at")
    }
    items: list[dict[str, Any]] = []
    for assignment in Assignment.objects.filter(status=AssignmentStatus.PUBLISHED).select_related("trainer")[:200]:
        decision = AccessControlAuditService.check(
            user=user,
            target_type=assignment.content_type,
            target_id=assignment.content_id,
            include_admin_override=False,
        )
        if not decision.get("allowed"):
            continue
        item = assignment_payload(assignment=assignment, submission=submissions.get(str(assignment.id)))
        item["access"] = {
            "allowed": bool(decision.get("allowed")),
            "code": decision.get("code"),
            "reason": decision.get("reason"),
        }
        items.append(item)
    return {
        "summary": {
            "total": len(items),
            "submitted": sum(1 for item in items if item.get("submission")),
            "pending": sum(1 for item in items if not item.get("submission")),
            "needs_revision": sum(1 for item in items if (item.get("submission") or {}).get("status") == "needs_revision"),
            "approved": sum(1 for item in items if (item.get("submission") or {}).get("status") == "approved"),
        },
        "items": items,
    }


def list_trainer_assignments(*, trainer) -> dict[str, Any]:
    assignment_filter = Q()
    if not getattr(trainer, "is_staff", False):
        assignment_filter = Q(trainer=trainer)
    queryset = (
        Assignment.objects.filter(assignment_filter)
        .select_related("trainer")
        .annotate(submissions_count=Count("submissions"), reviewed_count=Count("submissions", filter=Q(submissions__reviewed_at__isnull=False)))
        .order_by("-created_at")
    )
    items = []
    for assignment in queryset[:200]:
        item = assignment_payload(assignment=assignment)
        item["submissions_count"] = assignment.submissions_count
        item["reviewed_count"] = assignment.reviewed_count
        items.append(item)
    return {
        "summary": {
            "total": len(items),
            "published": sum(1 for item in items if item["status"] == AssignmentStatus.PUBLISHED),
            "draft": sum(1 for item in items if item["status"] == AssignmentStatus.DRAFT),
            "submissions": sum(int(item.get("submissions_count") or 0) for item in items),
        },
        "items": items,
    }


def list_trainer_submissions(*, trainer) -> dict[str, Any]:
    assignment_filter = Q(assignment__trainer=trainer)
    if getattr(trainer, "is_staff", False):
        assignment_filter = Q()
    submissions = (
        AssignmentSubmission.objects.filter(assignment_filter)
        .select_related("assignment", "student", "reviewed_by")
        .order_by("-submitted_at")[:200]
    )
    items = []
    for submission in submissions:
        payload = _submission_payload(submission)
        payload["assignment"] = assignment_payload(assignment=submission.assignment)
        items.append(payload)
    return {
        "summary": {
            "total": len(items),
            "submitted": sum(1 for item in items if item["status"] == "submitted"),
            "needs_revision": sum(1 for item in items if item["status"] == "needs_revision"),
            "approved": sum(1 for item in items if item["status"] == "approved"),
        },
        "items": items,
    }
