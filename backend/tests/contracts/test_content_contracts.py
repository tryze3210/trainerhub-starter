from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.trainer_profiles.services import ensure_trainer_public_profile
from apps.content.models import PublishedVideo


User = get_user_model()


def test_public_content_video_list_contract(db):
    user = User.objects.create_user(username='trainer', email='trainer@example.com', password='secret1234')
    trainer_profile = ensure_trainer_public_profile(user=user)
    PublishedVideo.objects.create(
        trainer_profile=trainer_profile,
        source_draft_id='11111111-1111-1111-1111-111111111111',
        slug='demo-video',
        title='Demo Video',
        description='demo',
        price_amount='9.99',
        currency='EUR',
    )
    client = APIClient()
    response = client.get('/api/v1/content/videos/')
    assert response.status_code == 200
    payload = response.json()
    assert payload[0]['slug'] == 'demo-video'
