from __future__ import annotations

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.ops.models import ReconciliationSnapshot
from apps.ops.reconciliation_snapshots import (
    get_reconciliation_snapshot_retention_policy,
    prune_reconciliation_snapshots,
)


def _snapshot(*, source: str, days_ago: int, marker: str) -> ReconciliationSnapshot:
    return ReconciliationSnapshot.objects.create(
        status=ReconciliationSnapshot.Status.OK,
        source=source,
        generated_at=timezone.now() - timedelta(days=days_ago),
        correlation_id=f'test-retention:{marker}',
        total_issues=0,
        critical_count=0,
        warning_count=0,
        info_count=0,
        summary={'total_issues': 0, 'critical_count': 0, 'warning_count': 0, 'info_count': 0},
        section_statuses={},
        report={'sections': {}},
    )


@pytest.mark.django_db
def test_reconciliation_snapshot_retention_preview_keeps_minimum_history_per_source():
    old_a = _snapshot(source=ReconciliationSnapshot.Source.SCHEDULED, days_ago=20, marker='old-a')
    old_b = _snapshot(source=ReconciliationSnapshot.Source.SCHEDULED, days_ago=15, marker='old-b')
    old_c = _snapshot(source=ReconciliationSnapshot.Source.SCHEDULED, days_ago=10, marker='old-c')
    latest = _snapshot(source=ReconciliationSnapshot.Source.SCHEDULED, days_ago=0, marker='latest')

    payload = get_reconciliation_snapshot_retention_policy(
        source=ReconciliationSnapshot.Source.SCHEDULED,
        scheduled_days=1,
        keep_min_per_source=1,
        max_candidates=10,
    )

    assert payload['status'] == 'preview'
    assert payload['summary']['candidate_count'] == 3
    assert {item['id'] for item in payload['candidates']} == {str(old_a.id), str(old_b.id), str(old_c.id)}
    assert str(latest.id) not in {item['id'] for item in payload['candidates']}
    assert ReconciliationSnapshot.objects.count() == 4


@pytest.mark.django_db
def test_reconciliation_snapshot_retention_prune_deletes_only_candidates():
    old = _snapshot(source=ReconciliationSnapshot.Source.SCHEDULED, days_ago=20, marker='old')
    latest = _snapshot(source=ReconciliationSnapshot.Source.SCHEDULED, days_ago=0, marker='latest')
    manual = _snapshot(source=ReconciliationSnapshot.Source.MANUAL, days_ago=400, marker='manual')

    payload = prune_reconciliation_snapshots(
        source=ReconciliationSnapshot.Source.SCHEDULED,
        scheduled_days=1,
        keep_min_per_source=1,
        max_candidates=10,
        dry_run=False,
    )

    assert payload['status'] == 'pruned'
    assert payload['summary']['deleted_count'] == 1
    assert not ReconciliationSnapshot.objects.filter(pk=old.pk).exists()
    assert ReconciliationSnapshot.objects.filter(pk=latest.pk).exists()
    assert ReconciliationSnapshot.objects.filter(pk=manual.pk).exists()


@pytest.mark.django_db
def test_reconciliation_snapshot_retention_endpoint_is_admin_only():
    user = get_user_model().objects.create_user(email='snapshot-retention-user@example.com', password='pass12345')
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get('/api/v1/ops/admin/reconciliation-snapshots/retention/')

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_preview_and_execute_reconciliation_snapshot_retention():
    admin = get_user_model().objects.create_superuser(
        email='snapshot-retention-admin@example.com',
        password='pass12345',
    )
    old = _snapshot(source=ReconciliationSnapshot.Source.SCHEDULED, days_ago=20, marker='endpoint-old')
    latest = _snapshot(source=ReconciliationSnapshot.Source.SCHEDULED, days_ago=0, marker='endpoint-latest')

    client = APIClient()
    client.force_authenticate(user=admin)

    preview = client.get(
        '/api/v1/ops/admin/reconciliation-snapshots/retention/?source=scheduled&scheduled_days=1&keep_min_per_source=1'
    )
    assert preview.status_code == 200
    assert preview.json()['status'] == 'preview'
    assert preview.json()['summary']['candidate_count'] == 1

    executed = client.post(
        '/api/v1/ops/admin/reconciliation-snapshots/retention/',
        {
            'source': 'scheduled',
            'scheduled_days': 1,
            'keep_min_per_source': 1,
            'dry_run': False,
        },
        format='json',
    )
    assert executed.status_code == 200
    assert executed.json()['status'] == 'pruned'
    assert not ReconciliationSnapshot.objects.filter(pk=old.pk).exists()
    assert ReconciliationSnapshot.objects.filter(pk=latest.pk).exists()
