import pytest
from rest_framework.test import APIClient

from apps.entitlements.models import Entitlement
from apps.users.models import User


@pytest.mark.django_db
def test_public_and_media_routes_are_published():
    client = APIClient()

    trainers_response = client.get('/api/v1/trainers/')
    assert trainers_response.status_code == 200

    catalog_response = client.get('/api/v1/public-catalog/items/')
    assert catalog_response.status_code == 200

    upload_intent_response = client.post(
        '/api/v1/videos/upload-intents/',
        {
            'filename': 'lesson.mp4',
            'content_type': 'video/mp4',
            'file_size_bytes': 1024,
            'visibility': 'private',
        },
        format='json',
    )
    assert upload_intent_response.status_code == 401


@pytest.mark.django_db
def test_entitlements_endpoint_returns_current_and_compatibility_fields():
    user = User.objects.create_user(email='entitlements@example.com', password='pass12345')
    entitlement = Entitlement.objects.create(
        user=user,
        kind=Entitlement.Kind.VIDEO,
        object_id='video-123',
        source=Entitlement.Source.ORDER,
        source_reference='order-123',
        is_active=True,
        metadata={'tier': 'basic'},
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get('/api/v1/entitlements/')
    assert response.status_code == 200
    payload = response.json()
    results = payload['results'] if isinstance(payload, dict) else payload
    row = results[0]
    assert row['id'] == str(entitlement.id)
    assert row['kind'] == 'video'
    assert row['object_id'] == 'video-123'
    assert row['source'] == 'order'
    assert row['source_reference'] == 'order-123'
    assert row['is_active'] is True
    assert row['source_type'] == 'order'
    assert row['target_type'] == 'video'
    assert row['target_id'] == 'video-123'
    assert row['source_order_id'] == 'order-123'
    assert row['source_subscription_id'] is None
    assert row['status'] == 'active'
