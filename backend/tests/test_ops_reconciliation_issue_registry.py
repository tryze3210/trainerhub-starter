from __future__ import annotations

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.ops.models import ReconciliationSnapshot
from apps.ops.reconciliation_snapshots import get_reconciliation_issue_registry


def _snapshot(*, minutes_ago: int, issues: list[dict], status: str = ReconciliationSnapshot.Status.DEGRADED) -> ReconciliationSnapshot:
    generated_at = timezone.now() - timedelta(minutes=minutes_ago)
    critical_count = sum(1 for issue in issues if issue.get('severity') == 'critical')
    warning_count = sum(1 for issue in issues if issue.get('severity') == 'warning')
    info_count = sum(1 for issue in issues if issue.get('severity') == 'info')
    return ReconciliationSnapshot.objects.create(
        status=status,
        source=ReconciliationSnapshot.Source.SCHEDULED,
        generated_at=generated_at,
        correlation_id=f'test-registry:{minutes_ago}',
        total_issues=len(issues),
        critical_count=critical_count,
        warning_count=warning_count,
        info_count=info_count,
        summary={
            'total_issues': len(issues),
            'critical_count': critical_count,
            'warning_count': warning_count,
            'info_count': info_count,
        },
        section_statuses={
            'outbox': {
                'status': status,
                'issue_count': len(issues),
                'critical_count': critical_count,
                'warning_count': warning_count,
                'info_count': info_count,
            }
        },
        report={
            'status': status,
            'summary': {'total_issues': len(issues)},
            'sections': {
                'outbox': {
                    'status': status,
                    'issue_count': len(issues),
                    'issues': issues,
                }
            },
        },
    )


@pytest.mark.django_db
def test_issue_registry_normalizes_snapshot_issues_and_repair_metadata():
    _snapshot(
        minutes_ago=30,
        issues=[
            {
                'code': 'outbox_delivery_problem',
                'severity': 'warning',
                'entity_type': 'outbox_message',
                'entity_id': 'outbox-old',
                'message': 'Old outbox issue.',
                'suggested_action': 'Retry outbox.',
                'related': [],
                'evidence': {'status': 'failed'},
            }
        ],
    )
    latest = _snapshot(
        minutes_ago=1,
        issues=[
            {
                'code': 'outbox_delivery_problem',
                'severity': 'critical',
                'entity_type': 'outbox_message',
                'entity_id': 'outbox-new',
                'message': 'Outbox message failed.',
                'suggested_action': 'Retry outbox.',
                'related': [],
                'evidence': {'status': 'dead'},
            },
            {
                'code': 'payment_webhook_problem',
                'severity': 'warning',
                'entity_type': 'payment_webhook',
                'entity_id': 'webhook-1',
                'message': 'Webhook is stuck.',
                'suggested_action': 'Reprocess webhook.',
                'related': [{'entity_type': 'payment', 'entity_id': 'payment-1', 'label': 'Payment'}],
                'evidence': {'status': 'processing'},
            },
        ],
    )

    payload = get_reconciliation_issue_registry(snapshot_id=str(latest.id))

    assert payload['status'] == ReconciliationSnapshot.Status.DEGRADED
    assert payload['snapshot']['id'] == str(latest.id)
    assert payload['summary']['total_count'] == 2
    assert payload['summary']['critical_count'] == 1
    assert payload['summary']['repairable_count'] == 2
    issue = payload['issues'][0]
    assert issue['issue_code'] == 'outbox_delivery_problem'
    assert issue['identity'] == 'outbox_delivery_problem:outbox_message:outbox-new'
    assert issue['repairable'] is True
    assert issue['repair_action'] == 'retry_outbox'
    assert issue['repair_entity_type'] == 'outbox_message'
    assert issue['repair_entity_id'] == 'outbox-new'
    assert issue['repair_policy_href'].startswith('/api/v1/ops/admin/reconciliation-repair/policy/')
    assert issue['state'] == 'introduced'


@pytest.mark.django_db
def test_issue_registry_filters_by_issue_code_and_repairable():
    _snapshot(
        minutes_ago=1,
        issues=[
            {
                'code': 'outbox_delivery_problem',
                'severity': 'warning',
                'entity_type': 'outbox_message',
                'entity_id': 'outbox-1',
                'message': 'Retryable.',
            },
            {
                'code': 'paid_order_without_successful_payment',
                'severity': 'critical',
                'entity_type': 'order',
                'entity_id': 'order-1',
                'message': 'Manual review required.',
            },
        ],
    )

    repairable_payload = get_reconciliation_issue_registry(repairable='true')
    assert repairable_payload['summary']['total_count'] == 1
    assert repairable_payload['issues'][0]['issue_code'] == 'outbox_delivery_problem'

    manual_payload = get_reconciliation_issue_registry(issue_code='paid_order_without_successful_payment')
    assert manual_payload['summary']['total_count'] == 1
    assert manual_payload['issues'][0]['repairable'] is False


@pytest.mark.django_db
def test_issue_registry_endpoint_is_admin_only():
    user = get_user_model().objects.create_user(email='issue-registry-user@example.com', password='pass12345')
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get('/api/v1/ops/admin/reconciliation-snapshots/issues/')

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_read_issue_registry_endpoint():
    admin = get_user_model().objects.create_superuser(email='issue-registry-admin@example.com', password='pass12345')
    _snapshot(
        minutes_ago=1,
        issues=[
            {
                'code': 'payment_webhook_problem',
                'severity': 'warning',
                'entity_type': 'payment_webhook',
                'entity_id': 'webhook-api-1',
                'message': 'Webhook failed.',
            }
        ],
    )

    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get('/api/v1/ops/admin/reconciliation-snapshots/issues/?repairable=true')

    assert response.status_code == 200
    payload = response.json()
    assert payload['summary']['total_count'] == 1
    assert payload['issues'][0]['repair_action'] == 'reprocess_webhook'
