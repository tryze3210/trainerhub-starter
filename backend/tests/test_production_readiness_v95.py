import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.ops.production_readiness import get_platform_production_readiness


@pytest.mark.django_db
def test_v110_production_readiness_reports_platform_gate_categories():
    payload = get_platform_production_readiness()

    assert payload['version'] == 'v110'
    assert payload['scope'] == 'full platform production readiness'
    categories = {check['category'] for check in payload['checks']}
    assert {'api_contract', 'python_contract', 'permissions', 'files', 'management_commands'}.issubset(categories)
    assert any(item['key'] == 'trainer_crm' for item in payload['frontend_surface'])
    assert any(item['key'] == 'trainer_schedule' for item in payload['frontend_surface'])
    assert any(item['key'] == 'messages' for item in payload['frontend_surface'])
    assert any(item['key'] == 'readiness_gate' for item in payload['smoke_commands'])
    assert any(item['key'] == 'launch_gate' for item in payload['smoke_commands'])
    assert any(item['role'] == 'trainer' for item in payload['role_matrix'])
    assert any(item['role'] == 'support' for item in payload['role_matrix'])
    assert any(item['role'] == 'finance' for item in payload['role_matrix'])
    assert any(item['role'] == 'readonly_auditor' for item in payload['role_matrix'])
    assert payload['ci_gate']['launch_script'] == 'scripts/ci/launch_gate.sh'


@pytest.mark.django_db
def test_admin_can_read_v110_production_readiness_endpoint():
    admin = get_user_model().objects.create_superuser(email='v95-admin@example.com', password='pass12345')
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get('/api/v1/ops/admin/production-readiness/')

    assert response.status_code == 200
    payload = response.json()
    assert payload['version'] == 'v110'
    assert 'summary' in payload
