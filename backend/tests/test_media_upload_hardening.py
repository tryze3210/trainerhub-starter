import pytest
from django.contrib.auth import get_user_model

from apps.videos.api.serializers import CompleteUploadSerializer, UploadIntentRequestSerializer
from apps.videos.models import MediaAsset
from apps.videos.tasks import verify_upload


def _payload(**overrides):
    payload = {
        "filename": "lesson.mp4",
        "content_type": "video/mp4",
        "file_size_bytes": 1024,
        "visibility": "private",
    }
    payload.update(overrides)
    return payload


def test_upload_intent_strips_path_components_from_filename():
    serializer = UploadIntentRequestSerializer(data=_payload(filename="../../lesson.mp4"))

    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["filename"] == "lesson.mp4"


@pytest.mark.parametrize(
    ("filename", "content_type"),
    [
        ("lesson.exe", "video/mp4"),
        ("cover.png", "image/jpeg"),
        ("clip.mp4", "image/webp"),
    ],
)
def test_upload_intent_rejects_mismatched_content_type_and_extension(filename, content_type):
    serializer = UploadIntentRequestSerializer(data=_payload(filename=filename, content_type=content_type))

    assert not serializer.is_valid()
    assert "filename" in serializer.errors


def test_upload_intent_rejects_files_above_configured_limit(settings):
    settings.MEDIA_MAX_UPLOAD_BYTES = 100
    serializer = UploadIntentRequestSerializer(data=_payload(file_size_bytes=101))

    assert not serializer.is_valid()
    assert "file_size_bytes" in serializer.errors


def test_complete_upload_normalizes_valid_sha256_checksum():
    checksum = "ABCDEF" + ("0" * 58)
    serializer = CompleteUploadSerializer(data={"checksum_sha256": checksum})

    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["checksum_sha256"] == checksum.lower()


def test_complete_upload_rejects_invalid_sha256_checksum():
    serializer = CompleteUploadSerializer(data={"checksum_sha256": "not-a-checksum"})

    assert not serializer.is_valid()
    assert "checksum_sha256" in serializer.errors


@pytest.mark.django_db
def test_verify_upload_skips_assets_that_are_not_uploaded(monkeypatch):
    user = get_user_model().objects.create_user(email="verify-skip@example.com", password="pass12345")
    asset = MediaAsset.objects.create(
        owner_user=user,
        bucket_name="private-media",
        object_key="videos/verify-skip.mp4",
        asset_type="video",
        visibility=MediaAsset.Visibility.PRIVATE,
        status=MediaAsset.Status.VERIFIED,
        content_type="video/mp4",
        file_size_bytes=1024,
    )

    def fail_head(*args, **kwargs):
        raise AssertionError("head_object must not be called for non-uploaded assets")

    monkeypatch.setattr("apps.videos.tasks.storage_service.head_object", fail_head)

    verify_upload(str(asset.id))

    asset.refresh_from_db()
    assert asset.status == MediaAsset.Status.VERIFIED
    assert asset.metadata_json["verify_skipped"] == "invalid_status"


@pytest.mark.django_db
def test_verify_upload_fails_when_storage_size_does_not_match_intent(monkeypatch):
    user = get_user_model().objects.create_user(email="verify-size@example.com", password="pass12345")
    asset = MediaAsset.objects.create(
        owner_user=user,
        bucket_name="private-media",
        object_key="videos/verify-size.mp4",
        asset_type="video",
        visibility=MediaAsset.Visibility.PRIVATE,
        status=MediaAsset.Status.UPLOADED,
        content_type="video/mp4",
        file_size_bytes=1024,
    )
    monkeypatch.setattr(
        "apps.videos.tasks.storage_service.head_object",
        lambda *args, **kwargs: {"ContentLength": 2048, "ContentType": "video/mp4"},
    )

    verify_upload(str(asset.id))

    asset.refresh_from_db()
    assert asset.status == MediaAsset.Status.FAILED
    assert asset.metadata_json["expected_content_length"] == 1024


@pytest.mark.django_db
def test_verify_upload_marks_matching_storage_object_verified(monkeypatch):
    user = get_user_model().objects.create_user(email="verify-ok@example.com", password="pass12345")
    asset = MediaAsset.objects.create(
        owner_user=user,
        bucket_name="private-media",
        object_key="videos/verify-ok.mp4",
        asset_type="video",
        visibility=MediaAsset.Visibility.PRIVATE,
        status=MediaAsset.Status.UPLOADED,
        content_type="video/mp4",
        file_size_bytes=1024,
    )
    monkeypatch.setattr(
        "apps.videos.tasks.storage_service.head_object",
        lambda *args, **kwargs: {"ContentLength": 1024, "ContentType": "video/mp4", "ETag": "etag-ok"},
    )

    verify_upload(str(asset.id))

    asset.refresh_from_db()
    assert asset.status == MediaAsset.Status.VERIFIED
    assert asset.metadata_json["content_length"] == 1024
    assert asset.metadata_json["etag"] == "etag-ok"
