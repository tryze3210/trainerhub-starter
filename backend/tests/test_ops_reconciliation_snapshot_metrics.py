from __future__ import annotations

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.ops.models import ReconciliationSnapshot
from apps.ops.reconciliation_snapshots import get_reconciliation_snapshot_metrics


def _section_payload(*, issue_count: int, critical_count: int = 0, status: str = 'degraded') -> dict:
    warning_count = max(issue_count - critical_count, 0)
    return {
        'payments': {
            'status': status,
            'issue_count': issue_count,
            'critical_count': critical_count,
            'warning_count': warning_count,
            'info_count': 0,
        }
    }


def _snapshot(
    *,
    total_issues: int,
    critical_count: int = 0,
    source: str = ReconciliationSnapshot.Source.MANUAL,
    status: str = ReconciliationSnapshot.Status.DEGRADED,
    minutes: int = 0,
) -> ReconciliationSnapshot:
    warning_count = max(total_issues - critical_count, 0)
    section_statuses = _section_payload(issue_count=total_issues, critical_count=critical_count, status=status)
    return ReconciliationSnapshot.objects.create(
        status=status,
        source=source,
        generated_at=timezone.now() + timedelta(minutes=minutes),
        correlation_id=f'test-metrics-{minutes}',
        total_issues=total_issues,
        critical_count=critical_count,
        warning_count=warning_count,
        info_count=0,
        summary={
            'total_issues': total_issues,
            'critical_count': critical_count,
            'warning_count': warning_count,
            'info_count': 0,
        },
        section_statuses=section_statuses,
        report={'sections': {'payments': {'status': status, 'issues': []}}},
    )


@pytest.mark.django_db
def test_reconciliation_snapshot_metrics_show_latest_delta_and_sections():
    _snapshot(total_issues=5, critical_count=1, minutes=1)
    latest = _snapshot(total_issues=2, critical_count=0, source=ReconciliationSnapshot.Source.REPAIR, minutes=2)

    payload = get_reconciliation_snapshot_metrics(limit=10)

    assert payload['status'] == latest.status
    assert payload['headline']['latest_snapshot_id'] == str(latest.id)
    assert payload['headline']['current_total_issues'] == 2
    assert payload['headline']['previous_total_issues'] == 5
    assert payload['headline']['total_issues_delta'] == -3
    assert payload['headline']['critical_count_delta'] == -1
    assert payload['headline']['direction'] == 'improved'
    assert payload['section_metrics'][0]['section'] == 'payments'
    assert payload['section_metrics'][0]['issue_count_delta'] == -3
    assert payload['repair_effectiveness']['improved_count'] == 1
    assert payload['trend']['count'] == 2


@pytest.mark.django_db
def test_admin_can_read_reconciliation_snapshot_metrics_endpoint():
    admin = get_user_model().objects.create_superuser(email='snapshot-metrics-admin@example.com', password='pass12345')
    _snapshot(total_issues=3, critical_count=1, minutes=1)
    _snapshot(total_issues=1, critical_count=0, source=ReconciliationSnapshot.Source.REPAIR, minutes=2)

    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get('/api/v1/ops/admin/reconciliation-snapshots/metrics/?limit=10')

    assert response.status_code == 200
    payload = response.json()
    assert payload['headline']['snapshot_count'] == 2
    assert payload['headline']['direction'] == 'improved'
    assert payload['distribution']['window_issue_totals']['total_issues'] == 4
    assert payload['trend']['points']


@pytest.mark.django_db
def test_reconciliation_snapshot_metrics_endpoint_is_admin_only():
    user = get_user_model().objects.create_user(email='snapshot-metrics-user@example.com', password='pass12345')
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get('/api/v1/ops/admin/reconciliation-snapshots/metrics/')

    assert response.status_code == 403
