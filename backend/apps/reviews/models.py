from django.db import models


class Review(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PUBLISHED = 'published'
    STATUS_REJECTED = 'rejected'
    STATUS_FLAGGED = 'flagged'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PUBLISHED, 'Published'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_FLAGGED, 'Flagged'),
    ]

    target_type = models.CharField(max_length=32)
    target_id = models.CharField(max_length=64)
    author_user_id = models.CharField(max_length=64)
    rating = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=160)
    body = models.TextField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)

    # Trust/quality read-model fields. They intentionally use primitive values instead of
    # foreign keys because reviews can point to multiple content domains and legacy rows.
    verified_purchase = models.BooleanField(default=False)
    entitlement_id = models.CharField(max_length=64, blank=True)
    trainer_id = models.CharField(max_length=64, blank=True)
    target_title = models.CharField(max_length=255, blank=True)
    target_slug = models.CharField(max_length=160, blank=True)
    quality_flags = models.JSONField(default=list, blank=True)
    moderation_note = models.TextField(blank=True)
    moderated_by_id = models.CharField(max_length=64, blank=True)
    moderated_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['target_type', 'target_id', 'status']),
            models.Index(fields=['author_user_id', 'target_type', 'target_id']),
            models.Index(fields=['trainer_id', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
        ordering = ['-created_at']
