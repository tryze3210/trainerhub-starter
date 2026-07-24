from celery import shared_task
from apps.videos.models import MediaAsset
from common.storage.client import storage_service


def _content_type_base(value: str) -> str:
    return (value or "").split(";", 1)[0].strip().lower()


def _fail_asset(asset: MediaAsset, *, reason: str, details: dict | None = None) -> str:
    asset.status = MediaAsset.Status.FAILED
    asset.metadata_json = {
        **asset.metadata_json,
        "verify_error": reason,
        **(details or {}),
    }
    asset.save(update_fields=["status", "metadata_json", "updated_at"])
    return str(asset.id)


@shared_task
def verify_upload(media_asset_id: str):
    asset = MediaAsset.objects.get(pk=media_asset_id)
    if asset.status != MediaAsset.Status.UPLOADED:
        asset.metadata_json = {
            **asset.metadata_json,
            "verify_skipped": "invalid_status",
            "verify_skipped_status": asset.status,
        }
        asset.save(update_fields=["metadata_json", "updated_at"])
        return str(asset.id)

    try:
        head = storage_service.head_object(asset.bucket_name, asset.object_key)
    except Exception as exc:
        return _fail_asset(asset, reason=str(exc))

    content_length = head.get("ContentLength")
    if content_length is None:
        return _fail_asset(asset, reason="Storage object is missing ContentLength.")
    try:
        actual_size = int(content_length)
    except (TypeError, ValueError):
        return _fail_asset(asset, reason="Storage object ContentLength is invalid.", details={"content_length": content_length})

    expected_size = int(asset.file_size_bytes or 0)
    if actual_size <= 0 or (expected_size > 0 and actual_size != expected_size):
        return _fail_asset(
            asset,
            reason="Storage object size does not match upload intent.",
            details={"content_length": actual_size, "expected_content_length": expected_size},
        )

    actual_content_type = _content_type_base(str(head.get("ContentType") or ""))
    expected_content_type = _content_type_base(asset.content_type)
    if actual_content_type and actual_content_type != expected_content_type:
        return _fail_asset(
            asset,
            reason="Storage object content type does not match upload intent.",
            details={"content_type": actual_content_type, "expected_content_type": expected_content_type},
        )

    asset.status = MediaAsset.Status.VERIFIED
    asset.metadata_json = {
        **asset.metadata_json,
        "etag": head.get("ETag"),
        "content_length": head.get("ContentLength"),
    }
    asset.save(update_fields=["status", "metadata_json", "updated_at"])
    return str(asset.id)
