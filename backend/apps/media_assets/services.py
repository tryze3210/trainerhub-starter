from __future__ import annotations

from uuid import uuid4

from common.storage.client import storage_service
from apps.media_assets.models import MediaAsset as LegacyMediaAsset
from apps.videos.models import MediaAsset as CanonicalMediaAsset


class MediaAssetService:
    bucket_name = 'trainerhub-media'

    def create_upload_session(self, *, trainer_id, asset_type: str, filename: str, title: str, content_type: str, user=None):
        key = f'trainers/{trainer_id}/{asset_type}/{uuid4()}-{filename}'
        upload = storage_service.create_presigned_upload(
            bucket=self.bucket_name,
            key=key,
            content_type=content_type,
            expires_in=900,
        )

        # Canonical media model used by videos/trainer_cms. The older media_assets
        # app remains as a route boundary, but upload sessions must return an id
        # that downstream video/CMS code can consume directly.
        canonical_asset = CanonicalMediaAsset.objects.create(
            owner_user=user,
            bucket_name=self.bucket_name,
            object_key=key,
            asset_type=asset_type,
            visibility=CanonicalMediaAsset.Visibility.PRIVATE,
            status=CanonicalMediaAsset.Status.DRAFT,
            content_type=content_type,
            original_filename=filename,
            metadata_json={'title': title, 'trainer_id': str(trainer_id)},
        )

        # Keep a lightweight legacy row for the old media-assets listing/status path.
        LegacyMediaAsset.objects.create(
            trainer_id=trainer_id,
            asset_type=asset_type,
            title=title,
            storage_bucket=self.bucket_name,
            storage_key=key,
            upload_status=LegacyMediaAsset.UploadStatus.CREATED,
            mime_type=content_type,
        )

        return {
            'asset_id': str(canonical_asset.id),
            'storage_key': canonical_asset.object_key,
            'upload': {
                **upload,
                'storage_key': canonical_asset.object_key,
            },
        }

    def mark_uploaded(self, asset: LegacyMediaAsset):
        asset.upload_status = LegacyMediaAsset.UploadStatus.UPLOADED
        asset.save(update_fields=['upload_status', 'updated_at'])
        return asset

    def mark_ready(self, asset: LegacyMediaAsset, *, duration_seconds: int | None = None):
        asset.upload_status = LegacyMediaAsset.UploadStatus.READY
        asset.duration_seconds = duration_seconds
        asset.save(update_fields=['upload_status', 'duration_seconds', 'updated_at'])
        return asset
