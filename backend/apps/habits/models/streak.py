from django.db import models
import uuid


class HabitStreakState(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    habit_plan_id = models.UUIDField(unique=True)
    user_id = models.UUIDField(db_index=True)
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_checkin_date = models.DateField(null=True, blank=True)
    freeze_tokens = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "habits_streak_state"
