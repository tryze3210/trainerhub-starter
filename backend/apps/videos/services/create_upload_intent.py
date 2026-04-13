import uuid
from django.conf import settings
from django.db import transaction
from apps.videos.models import MediaAsset
from common.storage.client import storage_service


class CreateUploadIntentService:
    @transaction.atomic
    def execute(self, *, user, filename: str, content_type: str, file_size_bytes: int, visibility: str):
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
        asset_type = "video" if content_type.startswith("video/") else "image"
        bucket_name = settings.VK_PRIVATE_BUCKET if visibility == "private" else settings.VK_PUBLIC_BUCKET
        asset = MediaAsset.objects.create(
            owner_user=user,
            bucket_name=bucket_name,
            object_key=f"users/{user.id}/{asset_type}s/{uuid.uuid4()}/original.{ext}",
            asset_type=asset_type,
            visibility=visibility,
            status=MediaAsset.Status.DRAFT,
            content_type=content_type,
            file_size_bytes=file_size_bytes,
            original_filename=filename,
        )
        upload = storage_service.create_presigned_upload(
            bucket=asset.bucket_name,
            key=asset.object_key,
            content_type=content_type,
            expires_in=settings.MEDIA_UPLOAD_TTL_SECONDS,
        )
        return asset, upload
