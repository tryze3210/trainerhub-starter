from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.ops.commerce_readiness import get_commerce_readiness


@pytest.mark.django_db
def test_commerce_readiness_contains_v841_to_v850_surface():
    payload = get_commerce_readiness()

    check_keys = {check['key'] for check in payload['checks']}
    api_keys = {item['key'] for item in payload['api_surface']}
    command_keys = {item['key'] for item in payload['management_commands']}
    frontend_keys = {item['key'] for item in payload['frontend_surface']}

    assert payload['version'] == 'v8.50'
    assert payload['scope'] == 'trainer commerce readiness'
    assert payload['status'] in {'ok', 'warning', 'degraded', 'critical'}

    assert 'trainer_revenue_summary' in check_keys
    assert 'trainer_payout_request' in check_keys
    assert 'trainer_analytics_overview' in check_keys
    assert 'trainer_products_list' in check_keys
    assert 'order_checkout' in check_keys
    assert 'subscription_lifecycle_policy' in check_keys
    assert 'entitlement_access_check' in check_keys
    assert 'trainer_onboarding_status' in check_keys
    assert 'trainer_revenue_summary' in api_keys
    assert 'check_commerce_readiness' in command_keys
    assert 'marketplace_catalog' in frontend_keys
    assert payload['summary']['total_checks'] == len(payload['checks'])


@pytest.mark.django_db
def test_admin_can_read_commerce_readiness_endpoint():
    admin = get_user_model().objects.create_superuser(email='commerce-readiness-admin@example.com', password='pass12345')
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get('/api/v1/ops/admin/commerce-readiness/?include_commands=true&include_frontend=true&include_recommendations=true')

    assert response.status_code == 200
    payload = response.json()
    assert payload['version'] == 'v8.50'
    assert payload['scope'] == 'trainer commerce readiness'
    assert any(check['key'] == 'trainer_revenue_summary' for check in payload['checks'])
    assert any(command['key'] == 'frontend_build' for command in payload['smoke_commands'])
    assert any(item['key'] == 'marketplace_catalog' for item in payload['frontend_surface'])


@pytest.mark.django_db
def test_commerce_readiness_endpoint_is_admin_only():
    user = get_user_model().objects.create_user(email='commerce-readiness-user@example.com', password='pass12345')
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get('/api/v1/ops/admin/commerce-readiness/')

    assert response.status_code == 403


@pytest.mark.django_db
def test_check_commerce_readiness_management_command_outputs_json(capsys):
    call_command('check_commerce_readiness', as_json=True, no_commands=True, no_frontend=True, no_recommendations=True)

    out = capsys.readouterr().out
    assert '"version": "v8.50"' in out
    assert '"trainer commerce readiness"' in out
    assert '"checks"' in out
