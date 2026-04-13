from django.db import models
import uuid


class HabitPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    cohort_id = models.UUIDField(null=True, blank=True, db_index=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=120)
    category = models.CharField(max_length=64, default="general")
    cadence = models.CharField(max_length=32, default="daily")
    target_value = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit = models.CharField(max_length=32, default="times")
    is_active = models.BooleanField(default=True)
    starts_at = models.DateField(null=True, blank=True)
    ends_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "habits_habit_plan"
        indexes = [
            models.Index(fields=["user_id", "is_active"]),
            models.Index(fields=["cohort_id"]),
        ]
