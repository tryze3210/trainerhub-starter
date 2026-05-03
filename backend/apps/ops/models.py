from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from django.conf import settings
from django.db import models
from django.utils import timezone as django_timezone

from apps.common.db import UUIDModel


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class DiagnosticsCheck:
    key: str
    title: str
    status: str
    severity: str
    message: str
    owner: str
    updated_at: str = field(default_factory=utcnow_iso)


@dataclass(slots=True)
class DiagnosticsRun:
    id: str
    suite_key: str
    triggered_by: str
    status: str
    started_at: str = field(default_factory=utcnow_iso)
    completed_at: str | None = None
    checks: list[dict] = field(default_factory=list)


class ReconciliationSnapshot(UUIDModel):
    """Persisted point-in-time reconciliation report.

    The live reconciliation report is intentionally read-only and relatively
    expensive because it cross-checks payments, orders, entitlements, payouts,
    webhooks and outbox state. A snapshot lets operators compare drift over time
    and verify whether repair actions are reducing issues.
    """

    class Status(models.TextChoices):
        OK = 'ok', 'OK'
        DEGRADED = 'degraded', 'Degraded'
        CRITICAL = 'critical', 'Critical'

    class Source(models.TextChoices):
        MANUAL = 'manual', 'Manual'
        SCHEDULED = 'scheduled', 'Scheduled'
        REPAIR = 'repair', 'Repair'
        CI = 'ci', 'CI'

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OK)
    source = models.CharField(max_length=16, choices=Source.choices, default=Source.MANUAL)
    generated_at = models.DateTimeField(default=django_timezone.now)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reconciliation_snapshots',
    )
    correlation_id = models.CharField(max_length=128, blank=True)

    total_issues = models.PositiveIntegerField(default=0)
    critical_count = models.PositiveIntegerField(default=0)
    warning_count = models.PositiveIntegerField(default=0)
    info_count = models.PositiveIntegerField(default=0)

    summary = models.JSONField(default=dict, blank=True)
    section_statuses = models.JSONField(default=dict, blank=True)
    report = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-generated_at', '-created_at']
        indexes = [
            models.Index(fields=['status', 'generated_at'], name='ops_rec_status_idx'),
            models.Index(fields=['source', 'generated_at'], name='ops_rec_source_idx'),
            models.Index(fields=['generated_at'], name='ops_rec_gen_idx'),
            models.Index(fields=['critical_count', 'total_issues'], name='ops_rec_counts_idx'),
        ]
