from django.db import models
import uuid


class UserHabitSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(unique=True)
    active_habits = models.PositiveIntegerField(default=0)
    completed_today = models.PositiveIntegerField(default=0)
    missed_today = models.PositiveIntegerField(default=0)
    aggregate_current_streak = models.PositiveIntegerField(default=0)
    aggregate_longest_streak = models.PositiveIntegerField(default=0)
    completion_rate_7d = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    completion_rate_30d = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "habits_user_snapshot"
