from dataclasses import asdict
from apps.media_assets.models import MediaAsset
from apps.media_assets.storage import VKCloudStorageSigner


class MediaAssetService:
    signer = VKCloudStorageSigner()

    def create_upload_session(self, *, trainer_id, asset_type: str, filename: str, title: str, content_type: str):
        presigned = self.signer.build_video_upload(str(trainer_id), filename, content_type)
        asset = MediaAsset.objects.create(
            trainer_id=trainer_id,
            asset_type=asset_type,
            title=title,
            storage_bucket="trainerhub-media",
            storage_key=presigned.storage_key,
            upload_status=MediaAsset.UploadStatus.CREATED,
            mime_type=content_type,
        )
        return {
            "asset_id": str(asset.id),
            "storage_key": asset.storage_key,
            "upload": asdict(presigned),
        }

    def mark_uploaded(self, asset: MediaAsset):
        asset.upload_status = MediaAsset.UploadStatus.UPLOADED
        asset.save(update_fields=["upload_status", "updated_at"])
        return asset

    def mark_ready(self, asset: MediaAsset, *, duration_seconds: int | None = None):
        asset.upload_status = MediaAsset.UploadStatus.READY
        asset.duration_seconds = duration_seconds
        asset.save(update_fields=["upload_status", "duration_seconds", "updated_at"])
        return asset
