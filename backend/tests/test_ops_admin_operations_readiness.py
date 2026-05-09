from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.ops.operations_readiness import get_ops_production_readiness


@pytest.mark.django_db
def test_ops_production_readiness_contains_v830_to_v840_surface():
    payload = get_ops_production_readiness()

    check_keys = {check['key'] for check in payload['checks']}
    api_keys = {item['key'] for item in payload['api_surface']}
    command_keys = {item['key'] for item in payload['management_commands']}

    assert payload['version'] == 'v8.40'
    assert payload['status'] in {'ok', 'warning', 'degraded', 'critical'}
    assert 'repair_snapshot_capture' in check_keys
    assert 'snapshot_compare' in check_keys
    assert 'snapshot_metrics' in check_keys
    assert 'snapshot_alerts' in check_keys
    assert 'issue_registry' in check_keys
    assert 'operations_hub' in check_keys
    assert 'operations_readiness' in check_keys
    assert 'operations_readiness' in api_keys
    assert 'check_ops_readiness' in command_keys
    assert payload['summary']['total_checks'] == len(payload['checks'])


@pytest.mark.django_db
def test_admin_can_read_ops_production_readiness_endpoint():
    admin = get_user_model().objects.create_superuser(email='ops-readiness-admin@example.com', password='pass12345')
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get('/api/v1/ops/admin/operations-readiness/?include_commands=true&include_recommendations=true')

    assert response.status_code == 200
    payload = response.json()
    assert payload['version'] == 'v8.40'
    assert payload['scope'] == 'ops/reconciliation production readiness'
    assert any(check['key'] == 'operations_hub' for check in payload['checks'])
    assert any(command['key'] == 'frontend_build' for command in payload['smoke_commands'])


@pytest.mark.django_db
def test_ops_production_readiness_endpoint_is_admin_only():
    user = get_user_model().objects.create_user(email='ops-readiness-user@example.com', password='pass12345')
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get('/api/v1/ops/admin/operations-readiness/')

    assert response.status_code == 403


@pytest.mark.django_db
def test_check_ops_readiness_management_command_outputs_json(capsys):
    call_command('check_ops_readiness', as_json=True, no_commands=True, no_recommendations=True)

    out = capsys.readouterr().out
    assert '"version": "v8.40"' in out
    assert '"checks"' in out
