from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.ops.models import ReconciliationSnapshot
from apps.ops.reconciliation_snapshots import (
    capture_reconciliation_snapshot_if_due,
    get_reconciliation_snapshot_schedule_status,
)


@pytest.mark.django_db
def test_scheduled_reconciliation_snapshot_capture_skips_when_recent_snapshot_exists():
    first = capture_reconciliation_snapshot_if_due(
        limit=10,
        source='scheduled',
        min_age_minutes=60,
        force=True,
        correlation_id='test:scheduled:first',
    )
    assert first['status'] == 'captured'
    assert first['captured'] is True
    assert first['snapshot']['source'] == ReconciliationSnapshot.Source.SCHEDULED

    second = capture_reconciliation_snapshot_if_due(
        limit=10,
        source='scheduled',
        min_age_minutes=60,
        correlation_id='test:scheduled:second',
    )
    assert second['status'] == 'skipped'
    assert second['captured'] is False
    assert second['reason'] == 'snapshot_not_due'
    assert second['latest_snapshot']['id'] == first['snapshot']['id']
    assert ReconciliationSnapshot.objects.filter(source=ReconciliationSnapshot.Source.SCHEDULED).count() == 1


@pytest.mark.django_db
def test_scheduled_reconciliation_snapshot_status_marks_empty_state_as_due():
    status = get_reconciliation_snapshot_schedule_status(source='scheduled', min_age_minutes=60)
    assert status['status'] == 'due'
    assert status['is_due'] is True
    assert status['latest_snapshot'] is None


@pytest.mark.django_db
def test_scheduled_reconciliation_snapshot_task_uses_idempotency_guard():
    from apps.ops.tasks import capture_reconciliation_snapshot_task

    first = capture_reconciliation_snapshot_task(
        limit=10,
        source='scheduled',
        min_age_minutes=60,
        force=True,
        correlation_id='test:task:first',
    )
    assert first['status'] == 'captured'

    second = capture_reconciliation_snapshot_task(
        limit=10,
        source='scheduled',
        min_age_minutes=60,
        correlation_id='test:task:second',
    )
    assert second['status'] == 'skipped'
    assert ReconciliationSnapshot.objects.filter(source=ReconciliationSnapshot.Source.SCHEDULED).count() == 1


@pytest.mark.django_db
def test_admin_can_read_reconciliation_snapshot_schedule_state():
    admin = get_user_model().objects.create_superuser(
        email='ops-snapshot-schedule-admin@example.com',
        password='pass12345',
    )
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get('/api/v1/ops/admin/reconciliation-snapshots/schedule/?source=scheduled&min_age_minutes=60')

    assert response.status_code == 200
    payload = response.json()
    assert payload['source'] == 'scheduled'
    assert payload['min_age_minutes'] == 60
    assert payload['status'] in {'due', 'fresh'}
    assert 'is_due' in payload
    assert 'next_due_at' in payload
