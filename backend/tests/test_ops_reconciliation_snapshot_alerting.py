from __future__ import annotations

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent
from apps.notifications.models import Notification
from apps.ops.models import ReconciliationSnapshot
from apps.ops.reconciliation_snapshots import (
    emit_reconciliation_snapshot_alerts,
    evaluate_reconciliation_snapshot_alerts,
)


def _snapshot(
    *,
    status: str,
    total_issues: int,
    critical_count: int,
    minutes_ago: int,
    source: str = ReconciliationSnapshot.Source.SCHEDULED,
) -> ReconciliationSnapshot:
    generated_at = timezone.now() - timedelta(minutes=minutes_ago)
    return ReconciliationSnapshot.objects.create(
        status=status,
        source=source,
        generated_at=generated_at,
        correlation_id=f'test-alert:{source}:{minutes_ago}',
        total_issues=total_issues,
        critical_count=critical_count,
        warning_count=max(total_issues - critical_count, 0),
        info_count=0,
        summary={
            'total_issues': total_issues,
            'critical_count': critical_count,
            'warning_count': max(total_issues - critical_count, 0),
            'info_count': 0,
        },
        section_statuses={
            'payments': {
                'status': status,
                'issue_count': total_issues,
                'critical_count': critical_count,
                'warning_count': max(total_issues - critical_count, 0),
                'info_count': 0,
            }
        },
        report={'sections': {}},
    )


@pytest.mark.django_db
def test_reconciliation_snapshot_alerts_detect_degraded_and_worsened_delta():
    previous = _snapshot(status=ReconciliationSnapshot.Status.OK, total_issues=1, critical_count=0, minutes_ago=30)
    latest = _snapshot(status=ReconciliationSnapshot.Status.DEGRADED, total_issues=4, critical_count=1, minutes_ago=1)

    payload = evaluate_reconciliation_snapshot_alerts(source=ReconciliationSnapshot.Source.SCHEDULED)

    assert payload['has_alerts'] is True
    assert payload['latest_snapshot']['id'] == str(latest.id)
    assert payload['previous_snapshot']['id'] == str(previous.id)
    assert payload['delta']['total_issues_delta'] == 3
    codes = {item['code'] for item in payload['alerts']}
    assert 'reconciliation_snapshot_degraded' in codes
    assert 'reconciliation_total_issues_increased' in codes
    assert 'reconciliation_critical_issues_increased' in codes


@pytest.mark.django_db
def test_reconciliation_snapshot_alert_emission_creates_audit_and_admin_notifications():
    admin = get_user_model().objects.create_superuser(email='snapshot-alert-admin@example.com', password='pass12345')
    regular = get_user_model().objects.create_user(email='snapshot-alert-user@example.com', password='pass12345')
    _snapshot(status=ReconciliationSnapshot.Status.OK, total_issues=0, critical_count=0, minutes_ago=30)
    latest = _snapshot(status=ReconciliationSnapshot.Status.CRITICAL, total_issues=3, critical_count=2, minutes_ago=1)

    payload = emit_reconciliation_snapshot_alerts(source=ReconciliationSnapshot.Source.SCHEDULED, notify_admins=True)

    assert payload['has_alerts'] is True
    assert payload['emitted_count'] >= 1
    assert AuditEvent.objects.filter(entity_type='reconciliation_snapshot', entity_id=str(latest.id)).exists()
    admin_notifications = list(Notification.objects.filter(user=admin))
    regular_notifications = list(Notification.objects.filter(user=regular))
    assert any((item.metadata or {}).get('source') == 'ops.reconciliation' for item in admin_notifications)
    assert not any((item.metadata or {}).get('source') == 'ops.reconciliation' for item in regular_notifications)


@pytest.mark.django_db
def test_reconciliation_snapshot_alert_endpoint_is_admin_only():
    user = get_user_model().objects.create_user(email='snapshot-alert-non-admin@example.com', password='pass12345')
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get('/api/v1/ops/admin/reconciliation-snapshots/alerts/')

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_evaluate_and_emit_reconciliation_snapshot_alerts():
    admin = get_user_model().objects.create_superuser(email='snapshot-alert-api-admin@example.com', password='pass12345')
    _snapshot(status=ReconciliationSnapshot.Status.OK, total_issues=0, critical_count=0, minutes_ago=30)
    _snapshot(status=ReconciliationSnapshot.Status.DEGRADED, total_issues=2, critical_count=1, minutes_ago=1)

    client = APIClient()
    client.force_authenticate(user=admin)

    evaluated = client.get('/api/v1/ops/admin/reconciliation-snapshots/alerts/?source=scheduled')
    assert evaluated.status_code == 200
    assert evaluated.json()['has_alerts'] is True

    emitted = client.post(
        '/api/v1/ops/admin/reconciliation-snapshots/alerts/',
        {'source': 'scheduled', 'notify_admins': True},
        format='json',
    )
    assert emitted.status_code == 202
    assert emitted.json()['emitted_count'] >= 1
