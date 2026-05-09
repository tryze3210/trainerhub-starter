from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_reconciliation_repair_dry_run_returns_policy_without_executing(monkeypatch):
    from apps.ops.repair import ReconciliationRepairService

    def fail_if_called(*args, **kwargs):  # pragma: no cover - assertion helper
        raise AssertionError('repair executor must not be called during dry_run')

    monkeypatch.setattr(ReconciliationRepairService, '_retry_outbox', fail_if_called)

    payload = ReconciliationRepairService().execute(
        action='retry_outbox',
        entity_type='outbox_message',
        entity_id='message-1',
        reason='preview retry before executing',
        dry_run=True,
    )

    assert payload['status'] == 'dry_run'
    assert payload['changed'] is False
    assert payload['result']['dry_run'] is True
    assert payload['repair_policy']['risk_level'] == 'low'
    assert payload['workflow']['dry_run'] is True
    assert payload['repair_snapshot']['status'] == 'skipped'
    assert payload['reconciliation_snapshot_id'] == ''


@pytest.mark.django_db
def test_high_risk_repair_requires_confirmation_token_before_execution(monkeypatch):
    from apps.ops import repair as repair_module
    from apps.ops.repair import (
        ReconciliationRepairService,
        RepairResult,
        make_reconciliation_repair_confirmation_token,
    )

    with pytest.raises(ValidationError) as exc_info:
        ReconciliationRepairService().execute(
            action='revoke_entitlement',
            entity_type='entitlement',
            entity_id='entitlement-1',
            reason='operator approved entitlement revocation',
        )
    assert 'confirm_token' in exc_info.value.detail

    token = make_reconciliation_repair_confirmation_token(
        action='revoke_entitlement',
        entity_type='entitlement',
        entity_id='entitlement-1',
    )

    def fake_log_admin_action(**kwargs):
        return SimpleNamespace(
            id=uuid4(),
            event_type=kwargs['action'],
            entity_type=kwargs['target_type'],
            entity_id=kwargs['target_id'],
            created_at=timezone.now(),
        )

    def fake_revoke(self, *, entity_type: str, entity_id: str, reason: str, force: bool):
        return RepairResult(
            action='revoke_entitlement',
            status='completed',
            entity_type=entity_type,
            entity_id=entity_id,
            message='Entitlement was revoked.',
            changed=True,
            result={'previous_status': 'active', 'entitlement_status': 'revoked', 'reason': reason},
        )

    def fake_capture(*, repair_payload, request=None, limit=100):
        return {
            'status': 'captured',
            'source': 'repair',
            'snapshot_id': 'snapshot-1',
            'href': '/admin/entities/reconciliation_snapshot/snapshot-1',
            'previous_problem_count': 3,
            'current_problem_count': 2,
            'problem_delta': -1,
            'improved': True,
        }

    monkeypatch.setattr(repair_module.AuditService, 'log_admin_action', staticmethod(fake_log_admin_action))
    monkeypatch.setattr(ReconciliationRepairService, '_revoke_entitlement', fake_revoke)
    monkeypatch.setattr('apps.ops.reconciliation_snapshots.capture_repair_reconciliation_snapshot', fake_capture)

    payload = ReconciliationRepairService().execute(
        action='revoke_entitlement',
        entity_type='entitlement',
        entity_id='entitlement-1',
        reason='operator approved entitlement revocation',
        confirm_token=token,
    )

    assert payload['status'] == 'completed'
    assert payload['repair_policy']['risk_level'] == 'high'
    assert payload['repair_policy']['requires_confirmation'] is True
    assert payload['workflow']['confirmation_passed'] is True
    assert payload['reconciliation_snapshot_id'] == 'snapshot-1'


@pytest.mark.django_db
def test_admin_can_read_reconciliation_repair_policy():
    admin = get_user_model().objects.create_superuser(email='repair-policy-admin@example.com', password='pass12345')
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get(
        '/api/v1/ops/admin/reconciliation-repair/policy/',
        {
            'action': 'reverse_payout_accrual',
            'entity_type': 'payment',
            'entity_id': 'payment-1',
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['policy']['risk_level'] == 'critical'
    assert payload['policy']['requires_confirmation'] is True
    assert payload['workflow']['confirmation_token']
    assert payload['workflow']['confirmation_token_subject'] == 'reverse_payout_accrual:payment:payment-1'
