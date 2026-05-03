import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_admin_operations_dashboard_is_admin_only():
    user = get_user_model().objects.create_user(email='ops-user@example.com', password='pass12345')
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get('/api/v1/ops/admin/operations-dashboard/')

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_read_operations_dashboard():
    admin = get_user_model().objects.create_superuser(email='ops-admin@example.com', password='pass12345')
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get('/api/v1/ops/admin/operations-dashboard/')

    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] in {'ok', 'degraded', 'critical'}
    assert set(payload['sections'].keys()) == {'outbox', 'webhooks', 'payments', 'payouts', 'moderation'}
    assert 'critical_count' in payload['summary']
    assert 'warning_count' in payload['summary']
