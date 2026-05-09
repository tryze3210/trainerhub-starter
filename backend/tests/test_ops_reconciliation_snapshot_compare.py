from __future__ import annotations

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.ops.models import ReconciliationSnapshot
from apps.ops.reconciliation_snapshots import ReconciliationSnapshotService


def _issue(code: str, severity: str, entity_type: str, entity_id: str) -> dict:
    return {
        'code': code,
        'severity': severity,
        'entity_type': entity_type,
        'entity_id': entity_id,
        'message': f'{code} on {entity_type}:{entity_id}',
        'suggested_action': 'repair through admin ops',
        'related': [],
        'evidence': {'entity_id': entity_id},
    }


def _snapshot(*, generated_at, source: str, issues: list[dict]) -> ReconciliationSnapshot:
    severity_counts = {'critical': 0, 'warning': 0, 'info': 0}
    for issue in issues:
        severity_counts[issue['severity']] = severity_counts.get(issue['severity'], 0) + 1

    status = 'critical' if severity_counts['critical'] else 'degraded' if issues else 'ok'
    summary = {
        'total_issues': len(issues),
        'critical_count': severity_counts['critical'],
        'warning_count': severity_counts['warning'],
        'info_count': severity_counts['info'],
        'by_severity': {key: value for key, value in severity_counts.items() if value},
    }
    section_statuses = {
        'orders': {
            'status': status,
            'issue_count': len(issues),
            'critical_count': severity_counts['critical'],
            'warning_count': severity_counts['warning'],
            'info_count': severity_counts['info'],
        }
    }
    report = {
        'status': status,
        'generated_at': generated_at.isoformat(),
        'summary': summary,
        'sections': {
            'orders': {
                'status': status,
                'metrics': {},
                'checks': [],
                'issue_count': len(issues),
                'issues': issues,
            }
        },
    }
    return ReconciliationSnapshot.objects.create(
        status=status,
        source=source,
        generated_at=generated_at,
        total_issues=summary['total_issues'],
        critical_count=summary['critical_count'],
        warning_count=summary['warning_count'],
        info_count=summary['info_count'],
        summary=summary,
        section_statuses=section_statuses,
        report=report,
    )


@pytest.mark.django_db
def test_reconciliation_snapshot_service_compares_latest_against_previous():
    now = timezone.now()
    baseline = _snapshot(
        generated_at=now - timedelta(minutes=10),
        source='manual',
        issues=[
            _issue('completed_order_without_active_entitlement', 'critical', 'order', 'order-1'),
            _issue('paid_order_without_successful_payment', 'warning', 'order', 'order-2'),
        ],
    )
    current = _snapshot(
        generated_at=now,
        source='manual',
        issues=[
            _issue('paid_order_without_successful_payment', 'warning', 'order', 'order-2'),
            _issue('active_entitlement_from_inactive_subscription', 'warning', 'entitlement', 'ent-3'),
        ],
    )

    payload = ReconciliationSnapshotService().compare(source='manual')

    assert payload['has_baseline'] is True
    assert payload['baseline_snapshot']['id'] == str(baseline.id)
    assert payload['current_snapshot']['id'] == str(current.id)
    assert payload['delta']['critical_count_delta'] == -1
    assert payload['delta']['direction'] == 'improved'
    assert payload['issue_diffs']['resolved_count'] == 1
    assert payload['issue_diffs']['introduced_count'] == 1
    assert payload['issue_diffs']['persisted_count'] == 1
    assert payload['issue_diffs']['resolved'][0]['entity_id'] == 'order-1'
    assert payload['issue_diffs']['introduced'][0]['entity_id'] == 'ent-3'


@pytest.mark.django_db
def test_admin_can_compare_reconciliation_snapshots_via_api():
    admin = get_user_model().objects.create_superuser(email='snapshot-compare-admin@example.com', password='pass12345')
    now = timezone.now()
    baseline = _snapshot(
        generated_at=now - timedelta(minutes=10),
        source='repair',
        issues=[_issue('payment_webhook_problem', 'critical', 'payment_webhook', 'wh-1')],
    )
    current = _snapshot(generated_at=now, source='repair', issues=[])

    client = APIClient()
    client.force_authenticate(user=admin)
    response = client.get(
        '/api/v1/ops/admin/reconciliation-snapshots/compare/',
        {'baseline_id': str(baseline.id), 'current_id': str(current.id), 'source': 'repair'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['baseline_snapshot']['id'] == str(baseline.id)
    assert payload['current_snapshot']['id'] == str(current.id)
    assert payload['issue_diffs']['resolved_count'] == 1
    assert payload['issue_diffs']['introduced_count'] == 0
    assert payload['delta']['total_issues_delta'] == -1
    assert payload['delta']['direction'] == 'improved'


@pytest.mark.django_db
def test_admin_can_read_latest_reconciliation_snapshot_by_source():
    admin = get_user_model().objects.create_superuser(email='snapshot-latest-admin@example.com', password='pass12345')
    now = timezone.now()
    older = _snapshot(generated_at=now - timedelta(minutes=20), source='repair', issues=[])
    latest = _snapshot(
        generated_at=now,
        source='repair',
        issues=[_issue('outbox_delivery_problem', 'warning', 'outbox_message', 'outbox-1')],
    )
    _snapshot(
        generated_at=now + timedelta(minutes=1),
        source='manual',
        issues=[_issue('manual_only_issue', 'critical', 'order', 'manual-order')],
    )

    client = APIClient()
    client.force_authenticate(user=admin)
    response = client.get('/api/v1/ops/admin/reconciliation-snapshots/latest/?source=repair')

    assert response.status_code == 200
    payload = response.json()
    assert payload['snapshot']['id'] == str(latest.id)
    assert payload['snapshot']['delta']['previous_snapshot_id'] == str(older.id)
    assert payload['snapshot']['source'] == 'repair'
