from django.db import models
import uuid


class ProgressJournalEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    habit_plan_id = models.UUIDField(null=True, blank=True, db_index=True)
    cohort_id = models.UUIDField(null=True, blank=True, db_index=True)
    entry_date = models.DateField(db_index=True)
    mood = models.CharField(max_length=32, blank=True, default="")
    energy = models.PositiveSmallIntegerField(default=0)
    body = models.TextField()
    visibility = models.CharField(max_length=32, default="private")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "habits_progress_journal_entry"
