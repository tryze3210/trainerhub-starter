from django.conf import settings
from django.db import models
from apps.common.db.models import TimeStampedModel


class VideoProgress(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='video_progress_records')
    video_id = models.CharField(max_length=64)
    watched_seconds = models.PositiveIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(default=0)
    completion_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_completed = models.BooleanField(default=False)
    last_position_seconds = models.PositiveIntegerField(default=0)
    last_watched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'progress_video_progress'
        indexes = [models.Index(fields=['user', 'video_id'])]
        constraints = [models.UniqueConstraint(fields=['user', 'video_id'], name='uniq_user_video_progress')]


class LessonProgress(TimeStampedModel):
    class ContentType(models.TextChoices):
        PROGRAM = 'program', 'Program'
        COURSE = 'course', 'Course'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lesson_progress_records')
    lesson_id = models.CharField(max_length=64)
    program_id = models.CharField(max_length=64)
    content_type = models.CharField(max_length=32, choices=ContentType.choices, default=ContentType.PROGRAM)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'progress_lesson_progress'
        indexes = [models.Index(fields=['user', 'content_type', 'program_id', 'is_completed'])]
        constraints = [models.UniqueConstraint(fields=['user', 'lesson_id'], name='uniq_user_lesson_progress')]


class ProgramProgress(TimeStampedModel):
    class ContentType(models.TextChoices):
        PROGRAM = 'program', 'Program'
        COURSE = 'course', 'Course'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='program_progress_records')
    program_id = models.CharField(max_length=64)
    content_type = models.CharField(max_length=32, choices=ContentType.choices, default=ContentType.PROGRAM)
    total_lessons = models.PositiveIntegerField(default=0)
    completed_lessons = models.PositiveIntegerField(default=0)
    completion_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_activity_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'progress_program_progress'
        indexes = [models.Index(fields=['user', 'content_type', 'program_id'])]
        constraints = [models.UniqueConstraint(fields=['user', 'program_id'], name='uniq_user_program_progress')]
