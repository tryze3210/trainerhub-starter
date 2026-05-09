from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.utils import timezone


@pytest.mark.django_db
def test_capture_repair_reconciliation_snapshot_compares_against_previous(monkeypatch):
    from apps.ops.models import ReconciliationSnapshot
    from apps.ops.reconciliation_snapshots import capture_repair_reconciliation_snapshot

    previous = ReconciliationSnapshot.objects.create(
        status=ReconciliationSnapshot.Status.CRITICAL,
        source=ReconciliationSnapshot.Source.MANUAL,
        total_issues=5,
        critical_count=2,
        warning_count=3,
        info_count=0,
        summary={'total_issues': 5, 'critical_count': 2, 'warning_count': 3, 'info_count': 0},
        section_statuses={},
        report={},
    )

    def fake_report(*, limit=100):
        return {
            'status': 'degraded',
            'generated_at': timezone.now(),
            'summary': {'total_issues': 3, 'critical_count': 1, 'warning_count': 2, 'info_count': 0},
            'sections': {},
        }

    monkeypatch.setattr('apps.ops.reconciliation_snapshots.get_money_reconciliation_report', fake_report)

    payload = capture_repair_reconciliation_snapshot(
        repair_payload={
            'action': 'retry_outbox',
            'status': 'accepted',
            'changed': True,
            'entity_type': 'outbox_message',
            'entity_id': 'msg-1',
            'audit_event_id': 'audit-1',
        },
        request=None,
    )

    created = ReconciliationSnapshot.objects.order_by('-generated_at', '-created_at').first()
    assert created is not None
    assert created.source == ReconciliationSnapshot.Source.REPAIR
    assert created.correlation_id == 'repair:audit-1'
    assert payload['snapshot_id'] == str(created.id)
    assert payload['previous_snapshot_id'] == str(previous.id)
    assert payload['previous_problem_count'] == 5
    assert payload['current_problem_count'] == 3
    assert payload['problem_delta'] == -2
    assert payload['critical_delta'] == -1
    assert payload['improved'] is True


def test_repair_execute_returns_snapshot_summary_without_hiding_repair_result(monkeypatch):
    from apps.ops import repair as repair_module
    from apps.ops.repair import ReconciliationRepairService, RepairResult

    def fake_log_admin_action(**kwargs):
        return SimpleNamespace(
            id=uuid4(),
            event_type=kwargs['action'],
            entity_type=kwargs['target_type'],
            entity_id=kwargs['target_id'],
            created_at=timezone.now(),
        )

    def fake_retry(self, *, entity_type: str, entity_id: str, reason: str):
        return RepairResult(
            action='retry_outbox',
            status='accepted',
            entity_type=entity_type,
            entity_id=entity_id,
            message='Outbox message was returned to pending state.',
            changed=True,
            result={'outbox_status': 'pending', 'reason': reason},
        )

    def fake_capture(*, repair_payload, request=None, limit=100):
        return {
            'status': 'captured',
            'source': 'repair',
            'snapshot_id': 'snapshot-1',
            'href': '/admin/entities/reconciliation_snapshot/snapshot-1',
            'previous_problem_count': 4,
            'current_problem_count': 2,
            'problem_delta': -2,
            'improved': True,
        }

    monkeypatch.setattr(repair_module.AuditService, 'log_admin_action', staticmethod(fake_log_admin_action))
    monkeypatch.setattr(ReconciliationRepairService, '_retry_outbox', fake_retry)
    monkeypatch.setattr('apps.ops.reconciliation_snapshots.capture_repair_reconciliation_snapshot', fake_capture)

    payload = ReconciliationRepairService().execute(
        action='retry_outbox',
        entity_type='outbox_message',
        entity_id='msg-1',
        reason='test repair',
        request=None,
    )

    assert payload['status'] == 'accepted'
    assert payload['repair_snapshot']['source'] == 'repair'
    assert payload['reconciliation_snapshot_id'] == 'snapshot-1'
    assert payload['previous_problem_count'] == 4
    assert payload['current_problem_count'] == 2
    assert payload['problem_delta'] == -2
    assert payload['improved'] is True
