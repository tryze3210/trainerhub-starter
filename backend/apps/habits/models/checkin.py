from django.db import models
import uuid


class DailyCheckIn(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    habit_plan_id = models.UUIDField(db_index=True)
    user_id = models.UUIDField(db_index=True)
    checkin_date = models.DateField(db_index=True)
    value = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    status = models.CharField(max_length=32, default="completed")
    source = models.CharField(max_length=32, default="manual")
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "habits_daily_checkin"
        unique_together = [("habit_plan_id", "checkin_date")]
        indexes = [
            models.Index(fields=["user_id", "checkin_date"]),
        ]
