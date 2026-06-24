from django.conf import settings
from rest_framework.exceptions import PermissionDenied
from apps.entitlements.access_audit import AccessControlAuditService
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
        if user.is_authenticated:
            decision = AccessControlAuditService.check(
                user=user,
                target_type="video",
                target_id=str(video.id),
                include_admin_override=False,
            )
            if decision.get("allowed"):
                return storage_service.create_presigned_read(video.media_asset.bucket_name, video.media_asset.object_key, settings.MEDIA_READ_TTL_SECONDS)
            raise PermissionDenied(f"You do not have access to this video: {decision.get('code')}")
        raise PermissionDenied("Authentication is required to access this video.")
