from django.db import models


class Review(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PUBLISHED = 'published'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PUBLISHED, 'Published'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    target_type = models.CharField(max_length=32)
    target_id = models.CharField(max_length=64)
    author_user_id = models.CharField(max_length=64)
    rating = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=160)
    body = models.TextField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
