from django.conf import settings
from rest_framework.exceptions import PermissionDenied
from common.storage.client import storage_service
from apps.videos.models import Video


class IssueVideoAccessUrlService:
    def execute(self, *, user, video: Video) -> str:
        if user.is_authenticated and user.role == "admin":
            return storage_service.create_presigned_read(video.media_asset.bucket_name, video.media_asset.object_key, settings.MEDIA_READ_TTL_SECONDS)
        if user.is_authenticated and user.role == "trainer" and hasattr(user, "trainer_profile") and video.trainer_id == user.trainer_profile.id:
            return storage_service.create_presigned_read(video.media_asset.bucket_name, video.media_asset.object_key, settings.MEDIA_READ_TTL_SECONDS)
        if video.is_free:
            return storage_service.create_presigned_read(video.media_asset.bucket_name, video.media_asset.object_key, settings.MEDIA_READ_TTL_SECONDS)
        if user.is_authenticated and hasattr(user, "customer_profile"):
            from apps.purchases.models import Purchase
            from apps.products.models import ProductItem
            has_paid_access = Purchase.objects.filter(
                customer=user.customer_profile,
                status="paid",
                product__items__video=video,
            ).exists()
            if has_paid_access:
                return storage_service.create_presigned_read(video.media_asset.bucket_name, video.media_asset.object_key, settings.MEDIA_READ_TTL_SECONDS)
        raise PermissionDenied("You do not have access to this video.")
