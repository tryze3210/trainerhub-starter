import pytest
from rest_framework.test import APIClient

from apps.trainers.models import TrainerProfile
from apps.videos.models import MediaAsset


@pytest.mark.django_db
def test_videos_routes_are_published(client):
    response = client.get('/api/v1/videos/')
    assert response.status_code in {200, 401, 403}


@pytest.mark.django_db
def test_media_assets_routes_are_published(client):
    response = client.get('/api/v1/media-assets/assets/')
    assert response.status_code in {401, 403}


@pytest.mark.django_db
def test_legacy_media_upload_session_uses_canonical_videos_media_asset(monkeypatch, user_factory):
    user = user_factory(email='trainer@example.com', role='trainer')
    TrainerProfile.objects.create(
        user=user,
        slug='trainer-one',
        display_name='Trainer One',
        status='active',
    )

    def fake_upload(*, bucket, key, content_type, expires_in=900):
        return {
            'url': f'https://storage.example/{bucket}/{key}',
            'method': 'PUT',
            'headers': {'Content-Type': content_type},
            'expires_in': expires_in,
        }

    monkeypatch.setattr('common.storage.client.storage_service.create_presigned_upload', fake_upload)

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.post(
        '/api/v1/media-assets/assets/upload-session/',
        {
            'asset_type': 'video',
            'filename': 'lesson.mp4',
            'title': 'Lesson 1',
            'content_type': 'video/mp4',
        },
        format='json',
    )

    assert response.status_code == 201
    asset = MediaAsset.objects.get(id=response.data['asset_id'])
    assert asset.owner_user_id == user.id
    assert asset.original_filename == 'lesson.mp4'
    assert asset.metadata_json['title'] == 'Lesson 1'
    assert response.data['upload']['storage_key'] == asset.object_key


@pytest.mark.django_db
def test_trainer_cms_requires_verified_canonical_media_asset(user_factory):
    from apps.trainer_cms.models import TrainerVideoDraft
    from apps.trainer_cms.services import TrainerCMSService

    user = user_factory(email='trainer2@example.com', role='trainer')
    trainer = TrainerProfile.objects.create(
        user=user,
        slug='trainer-two',
        display_name='Trainer Two',
        status='active',
    )
    asset = MediaAsset.objects.create(
        owner_user=user,
        bucket_name='trainerhub-private',
        object_key='users/x/videos/y/original.mp4',
        asset_type='video',
        visibility=MediaAsset.Visibility.PRIVATE,
        status=MediaAsset.Status.VERIFIED,
        content_type='video/mp4',
        file_size_bytes=1024,
        original_filename='original.mp4',
    )
    draft = TrainerVideoDraft.objects.create(
        trainer_id=trainer.id,
        title='Draft video',
        slug='draft-video',
        video_asset_id=asset.id,
    )

    draft = TrainerCMSService().submit_video_for_review(draft)
    assert draft.status == 'review'
