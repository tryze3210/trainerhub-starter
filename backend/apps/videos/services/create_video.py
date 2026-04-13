from django.db import transaction
from rest_framework.exceptions import ValidationError
from apps.videos.models import MediaAsset, Video


class CreateVideoService:
    @transaction.atomic
    def execute(self, *, trainer, media_asset_id, slug: str, title: str, description: str = "", is_free: bool = False):
        asset = MediaAsset.objects.select_for_update().get(pk=media_asset_id, owner_user=trainer.user, is_deleted=False)
        if asset.asset_type != "video":
            raise ValidationError({"media_asset_id": "Asset must be a video."})
        if asset.status != MediaAsset.Status.VERIFIED:
            raise ValidationError({"media_asset_id": "Media asset must be verified before video creation."})
        if hasattr(asset, "video"):
            raise ValidationError({"media_asset_id": "Media asset is already attached to a video."})

        return Video.objects.create(
            trainer=trainer,
            media_asset=asset,
            slug=slug,
            title=title,
            description=description,
            is_free=is_free,
            status="ready",
            duration_seconds=asset.metadata_json.get("duration_seconds"),
        )
