from __future__ import annotations

from uuid import uuid4

from django.db import models
from django.utils import timezone


class DomainEvent(models.Model):
    """Persistent business event emitted by the modular monolith.

    Domain events are the source of truth for cross-module orchestration: payment
    success, entitlement grants, payout accrual, moderation decisions, media
    lifecycle changes and admin operations. Each event gets exactly one outbox
    message so delivery can be retried without re-running business logic.
    """

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    event_type = models.CharField(max_length=128, db_index=True)
    aggregate_type = models.CharField(max_length=96, db_index=True)
    aggregate_id = models.CharField(max_length=128, db_index=True)
    tenant_id = models.CharField(max_length=128, blank=True, null=True, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    idempotency_key = models.CharField(max_length=160, blank=True, null=True, unique=True)
    version = models.PositiveIntegerField(default=1)
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-occurred_at', '-created_at']
        indexes = [
            models.Index(fields=['event_type', 'occurred_at'], name='events_type_occurred_idx'),
            models.Index(fields=['aggregate_type', 'aggregate_id'], name='events_aggregate_idx'),
            models.Index(fields=['tenant_id', 'occurred_at'], name='events_tenant_time_idx'),
        ]

    def __str__(self) -> str:
        return f'{self.event_type}:{self.aggregate_type}:{self.aggregate_id}'


class OutboxMessage(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        PROCESSED = 'processed', 'Processed'
        FAILED = 'failed', 'Failed'
        DEAD = 'dead', 'Dead'

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    event = models.OneToOneField(DomainEvent, on_delete=models.CASCADE, related_name='outbox_message')
    topic = models.CharField(max_length=128, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PENDING, db_index=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=10)
    next_retry_at = models.DateTimeField(blank=True, null=True, db_index=True)
    locked_at = models.DateTimeField(blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['status', 'next_retry_at', 'created_at'], name='outbox_dispatch_idx'),
            models.Index(fields=['topic', 'status'], name='outbox_topic_status_idx'),
        ]

    def __str__(self) -> str:
        return f'{self.topic}:{self.status}:{self.id}'


class InboxMessage(models.Model):
    class Status(models.TextChoices):
        RECEIVED = 'received', 'Received'
        PROCESSING = 'processing', 'Processing'
        PROCESSED = 'processed', 'Processed'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    consumer = models.CharField(max_length=128)
    message_key = models.CharField(max_length=160)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.RECEIVED, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    received_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(blank=True, null=True)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-received_at', '-created_at']
        constraints = [
            models.UniqueConstraint(fields=['consumer', 'message_key'], name='uniq_inbox_consumer_message'),
        ]
        indexes = [
            models.Index(fields=['consumer', 'status'], name='inbox_consumer_status_idx'),
        ]

    def __str__(self) -> str:
        return f'{self.consumer}:{self.message_key}:{self.status}'
