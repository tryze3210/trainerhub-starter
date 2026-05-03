import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.ops.models import ReconciliationSnapshot
from apps.ops.reconciliation_snapshots import ReconciliationSnapshotService


@pytest.mark.django_db
def test_reconciliation_snapshot_service_captures_persisted_report():
    snapshot = ReconciliationSnapshotService().capture(source='scheduled', correlation_id='test-snapshot')

    assert snapshot['id']
    assert snapshot['source'] == 'scheduled'
    assert snapshot['correlation_id'] == 'test-snapshot'
    assert snapshot['summary']['total_issues'] >= 0
    assert ReconciliationSnapshot.objects.filter(pk=snapshot['id']).exists()


@pytest.mark.django_db
def test_admin_can_capture_and_list_reconciliation_snapshots():
    admin = get_user_model().objects.create_superuser(email='snapshot-admin@example.com', password='pass12345')
    client = APIClient()
    client.force_authenticate(user=admin)

    capture_response = client.post(
        '/api/v1/ops/admin/reconciliation-snapshots/capture/',
        {'limit': 25, 'source': 'manual', 'correlation_id': 'api-snapshot'},
        format='json',
    )
    assert capture_response.status_code == 201
    capture_payload = capture_response.json()
    assert capture_payload['id']
    assert capture_payload['source'] == 'manual'

    list_response = client.get('/api/v1/ops/admin/reconciliation-snapshots/?limit=10')
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload['count'] >= 1
    assert list_payload['snapshots'][0]['id'] == capture_payload['id']

    trend_response = client.get('/api/v1/ops/admin/reconciliation-snapshots/trend/?limit=10')
    assert trend_response.status_code == 200
    assert trend_response.json()['points']


@pytest.mark.django_db
def test_non_admin_cannot_capture_reconciliation_snapshot():
    user = get_user_model().objects.create_user(email='snapshot-user@example.com', password='pass12345')
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post('/api/v1/ops/admin/reconciliation-snapshots/capture/', {'limit': 25}, format='json')
    assert response.status_code == 403
