from django.db import models
from apps.core.models import UUIDModel, TimeStampedModel
from apps.users.models import User


class CustomerProfile(UUIDModel, TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="customer_profile")
    display_name = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    streak_count = models.PositiveIntegerField(default=0)


class CustomerSegment(UUIDModel, TimeStampedModel):
    trainer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="crm_segments")
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=24, blank=True)
    customers = models.ManyToManyField(CustomerProfile, related_name="crm_segments", blank=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["trainer", "name"], name="uniq_crm_segment_per_trainer_name"),
        ]

    def __str__(self):
        return f"{self.name} ({self.trainer_id})"


class CustomerNote(UUIDModel, TimeStampedModel):
    trainer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="crm_customer_notes")
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="trainer_crm_notes")
    body = models.TextField()
    visibility = models.CharField(max_length=24, default="trainer_private")
    pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ["-pinned", "-created_at"]
        indexes = [
            models.Index(fields=["trainer", "customer", "-created_at"], name="crm_note_trainer_customer_idx"),
        ]

    def __str__(self):
        return f"CRM note {self.id}"
