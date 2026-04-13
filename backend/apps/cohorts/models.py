import uuid
from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class GroupProgram(TimeStampedModel):
    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PUBLISHED, "Published"),
        (STATUS_ARCHIVED, "Archived"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trainer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="group_programs")
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    price_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, default="RUB")


class Cohort(TimeStampedModel):
    STATUS_DRAFT = "draft"
    STATUS_OPEN = "open"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_OPEN, "Open"),
        (STATUS_IN_PROGRESS, "In progress"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    program = models.ForeignKey(GroupProgram, on_delete=models.CASCADE, related_name="cohorts")
    code = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    capacity = models.PositiveIntegerField(default=0)
    timezone = models.CharField(max_length=64, default="Europe/Berlin")


class CohortEnrollment(TimeStampedModel):
    STATUS_PENDING = "pending"
    STATUS_ACTIVE = "active"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_REFUNDED = "refunded"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_REFUNDED, "Refunded"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE, related_name="enrollments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cohort_enrollments")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING)
    activated_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=64, blank=True)
    order_id = models.UUIDField(null=True, blank=True)

    class Meta:
        unique_together = [("cohort", "user")]


class ProgressCheckpoint(TimeStampedModel):
    TYPE_CONTENT = "content"
    TYPE_ATTENDANCE = "attendance"
    TYPE_TASK = "task"
    TYPE_MEASUREMENT = "measurement"
    TYPE_CHOICES = [
        (TYPE_CONTENT, "Content"),
        (TYPE_ATTENDANCE, "Attendance"),
        (TYPE_TASK, "Task"),
        (TYPE_MEASUREMENT, "Measurement"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE, related_name="checkpoints")
    title = models.CharField(max_length=255)
    checkpoint_type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    sequence = models.PositiveIntegerField(default=1)
    due_at = models.DateTimeField(null=True, blank=True)
    is_required = models.BooleanField(default=True)

    class Meta:
        ordering = ["sequence", "created_at"]


class EnrollmentCheckpointProgress(TimeStampedModel):
    STATUS_PENDING = "pending"
    STATUS_DONE = "done"
    STATUS_SKIPPED = "skipped"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_DONE, "Done"),
        (STATUS_SKIPPED, "Skipped"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(CohortEnrollment, on_delete=models.CASCADE, related_name="checkpoint_progress")
    checkpoint = models.ForeignKey(ProgressCheckpoint, on_delete=models.CASCADE, related_name="enrollment_progress")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING)
    completed_at = models.DateTimeField(null=True, blank=True)
    value_json = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [("enrollment", "checkpoint")]


class CohortDashboardSnapshot(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE, related_name="dashboard_snapshots")
    snapshot_date = models.DateField()
    enrolled_count = models.PositiveIntegerField(default=0)
    active_count = models.PositiveIntegerField(default=0)
    completed_count = models.PositiveIntegerField(default=0)
    completion_rate = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    avg_checkpoint_progress = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    attendance_rate = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    class Meta:
        unique_together = [("cohort", "snapshot_date")]
