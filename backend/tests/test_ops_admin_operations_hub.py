from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.ops.operations_hub import get_admin_operations_hub


BASE_DASHBOARD = {
    'status': 'degraded',
    'generated_at': timezone.now(),
    'sections': {
        'outbox': {
            'status': 'degraded',
            'issues': [{'code': 'outbox_stuck_processing', 'severity': 'warning', 'count': 2}],
            'counts': {'pending': 4, 'processing': 2, 'failed': 0, 'dead': 0, 'stuck_processing': 2},
            'recent_problem_messages': [],
        },
        'webhooks': {'status': 'ok', 'issues': [], 'counts': {'failed': 0, 'rejected': 0, 'stuck': 0}},
        'payments': {'status': 'ok', 'issues': [], 'counts': {'disputed': 0, 'charged_back': 0, 'refunded': 0}},
        'payouts': {'status': 'ok', 'issues': [], 'counts': {}, 'amounts': {'locked_total': '0.00'}},
        'moderation': {'status': 'ok', 'issues': [], 'counts': {}},
    },
    'summary': {'critical_count': 0, 'warning_count': 1, 'critical_items': [], 'warning_items': []},
}


METRICS = {
    'status': 'critical',
    'headline': {
        'latest_snapshot_id': 'snapshot-1',
        'latest_status': 'critical',
        'current_total_issues': 3,
        'current_critical_count': 1,
        'direction': 'worsened',
    },
    'trend': {'points': []},
}


SCHEDULE = {
    'status': 'ok',
    'due': False,
    'latest_generated_at': timezone.now().isoformat(),
    'next_capture_due_at': timezone.now().isoformat(),
}


ALERTS = {
    'status': 'critical',
    'has_alerts': True,
    'alerts': [{'code': 'reconciliation_critical_issues_increased', 'severity': 'critical'}],
}


ISSUES = {
    'status': 'critical',
    'summary': {'total_count': 3, 'critical_count': 1, 'warning_count': 2, 'repairable_count': 2},
    'issues': [
        {
            'identity': 'outbox_delivery_problem:outbox_message:1',
            'issue_code': 'outbox_delivery_problem',
            'severity': 'critical',
            'entity_type': 'outbox_message',
            'entity_id': '1',
            'repairable': True,
        }
    ],
}


@pytest.fixture(autouse=True)
def patch_hub_dependencies(monkeypatch):
    monkeypatch.setattr('apps.ops.operations_hub.get_admin_operations_dashboard', lambda: BASE_DASHBOARD)
    monkeypatch.setattr('apps.ops.operations_hub.get_reconciliation_snapshot_metrics', lambda **kwargs: METRICS)
    monkeypatch.setattr('apps.ops.operations_hub.get_reconciliation_snapshot_schedule', lambda **kwargs: SCHEDULE)
    monkeypatch.setattr('apps.ops.operations_hub.get_reconciliation_snapshot_alerts', lambda **kwargs: ALERTS)
    monkeypatch.setattr('apps.ops.operations_hub.get_reconciliation_issue_registry', lambda **kwargs: ISSUES)


@pytest.mark.django_db
def test_admin_operations_hub_consolidates_async_money_and_reconciliation():
    payload = get_admin_operations_hub(snapshot_limit=30, issue_limit=20)

    assert payload['status'] == 'critical'
    assert payload['summary']['operations_warning_count'] == 1
    assert payload['summary']['reconciliation_total_issues'] == 3
    assert payload['summary']['reconciliation_repairable_issues'] == 2
    assert payload['sections']['async_infra']['status'] == 'degraded'
    assert payload['sections']['money_risk']['status'] == 'ok'
    assert payload['sections']['reconciliation']['status'] == 'critical'
    assert any(action['key'] == 'capture_reconciliation_snapshot' for action in payload['quick_actions'])
    assert any(item['key'] == 'reconciliation_snapshots' for item in payload['navigation'])


@pytest.mark.django_db
@pytest.mark.parametrize('query', ['', '?snapshot_limit=10&issue_limit=5&source=scheduled'])
def test_admin_can_read_operations_hub_endpoint(query: str):
    admin = get_user_model().objects.create_superuser(email=f'ops-hub-admin{query or "default"}@example.com'.replace('?', '-').replace('&', '-').replace('=', '-'), password='pass12345')
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get(f'/api/v1/ops/admin/operations-hub/{query}')

    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'critical'
    assert payload['sections']['reconciliation']['issue_registry']['summary']['repairable_count'] == 2


@pytest.mark.django_db
def test_operations_hub_endpoint_is_admin_only():
    user = get_user_model().objects.create_user(email='ops-hub-user@example.com', password='pass12345')
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get('/api/v1/ops/admin/operations-hub/')

    assert response.status_code == 403
