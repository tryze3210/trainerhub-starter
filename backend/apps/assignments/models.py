import uuid

from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class AssignmentStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class AssignmentContentType(models.TextChoices):
    PROGRAM = "program", "Program"
    COURSE = "course", "Course"


class SubmissionStatus(models.TextChoices):
    SUBMITTED = "submitted", "Submitted"
    REVIEWED = "reviewed", "Reviewed"
    NEEDS_REVISION = "needs_revision", "Needs revision"
    APPROVED = "approved", "Approved"


class Assignment(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trainer_assignments",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    content_type = models.CharField(max_length=32, choices=AssignmentContentType.choices)
    content_id = models.CharField(max_length=80, db_index=True)
    lesson_id = models.CharField(max_length=80, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=AssignmentStatus.choices, default=AssignmentStatus.DRAFT)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "assignments_assignment"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["content_type", "content_id", "status"], name="asg_target_stat_idx"),
            models.Index(fields=["trainer", "status"], name="asg_trainer_stat_idx"),
        ]

    def __str__(self) -> str:
        return self.title


class AssignmentSubmission(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assignment_submissions",
    )
    answer_text = models.TextField(blank=True)
    attachments = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=32, choices=SubmissionStatus.choices, default=SubmissionStatus.SUBMITTED)
    submitted_at = models.DateTimeField()
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reviewed_assignment_submissions",
        null=True,
        blank=True,
    )
    review_comment = models.TextField(blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "assignments_submission"
        ordering = ["-submitted_at", "-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["assignment", "student"], name="uq_asg_sub_student"),
        ]
        indexes = [
            models.Index(fields=["student", "status"], name="asg_sub_stu_stat_idx"),
            models.Index(fields=["assignment", "status"], name="asg_sub_asg_stat_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.assignment_id}:{self.student_id}"