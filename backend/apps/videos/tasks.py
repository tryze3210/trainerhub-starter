from celery import shared_task
from apps.videos.models import MediaAsset
from common.storage.client import storage_service


@shared_task
def verify_upload(media_asset_id: str):
    asset = MediaAsset.objects.get(pk=media_asset_id)
    try:
        head = storage_service.head_object(asset.bucket_name, asset.object_key)
    except Exception as exc:
        asset.status = MediaAsset.Status.FAILED
        asset.metadata_json = {**asset.metadata_json, "verify_error": str(exc)}
        asset.save(update_fields=["status", "metadata_json", "updated_at"])
        return str(asset.id)

    asset.status = MediaAsset.Status.VERIFIED
    asset.metadata_json = {
        **asset.metadata_json,
        "etag": head.get("ETag"),
        "content_length": head.get("ContentLength"),
    }
    asset.save(update_fields=["status", "metadata_json", "updated_at"])
    return str(asset.id)
