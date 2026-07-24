from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, views
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from apps.access_control.permissions import CanUploadMedia, ROLE_TRAINER, user_role_set
from apps.videos.models import MediaAsset, Video
from apps.videos.services.create_upload_intent import CreateUploadIntentService
from apps.videos.services.create_video import CreateVideoService
from apps.videos.services.issue_access_url import IssueVideoAccessUrlService
from apps.videos.tasks import verify_upload
from common.permissions import IsTrainer
from .serializers import UploadIntentRequestSerializer, CompleteUploadSerializer, MediaAssetSerializer, VideoSerializer


def _trainer_profile_for(user):
    if not getattr(user, "is_authenticated", False):
        return None
    if ROLE_TRAINER not in user_role_set(user):
        return None
    return getattr(user, "trainer_profile", None)


class UploadIntentCreateApi(views.APIView):
    permission_classes = [permissions.IsAuthenticated, CanUploadMedia]

    def post(self, request):
        serializer = UploadIntentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        asset, upload = CreateUploadIntentService().execute(user=request.user, **serializer.validated_data)
        return Response(
            {
                "media_asset_id": str(asset.id),
                "object_key": asset.object_key,
                "upload_url": upload["url"],
                "upload_method": upload["method"],
                "required_headers": upload["headers"],
                "expires_in": upload["expires_in"],
            },
            status=status.HTTP_201_CREATED,
        )


class UploadIntentCompleteApi(views.APIView):
    permission_classes = [permissions.IsAuthenticated, CanUploadMedia]

    def post(self, request, media_asset_id):
        serializer = CompleteUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        asset = get_object_or_404(MediaAsset, pk=media_asset_id, owner_user=request.user, is_deleted=False)
        if asset.status != MediaAsset.Status.DRAFT:
            raise ValidationError({"media_asset_id": f"Upload can only be completed from draft status, got {asset.status}."})
        asset.status = MediaAsset.Status.UPLOADED
        checksum = serializer.validated_data.get("checksum_sha256")
        if checksum:
            asset.checksum_sha256 = checksum
        asset.save(update_fields=["status", "checksum_sha256", "updated_at"])
        verify_upload.delay(str(asset.id))
        return Response({"media_asset_id": str(asset.id), "status": asset.status})


class MediaAssetDetailApi(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, media_asset_id):
        asset = get_object_or_404(MediaAsset, pk=media_asset_id, owner_user=request.user, is_deleted=False)
        return Response(MediaAssetSerializer(asset).data)


class VideoListCreateApi(generics.ListCreateAPIView):
    serializer_class = VideoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Video.objects.filter(is_deleted=False).select_related("trainer", "media_asset")
        trainer_profile = _trainer_profile_for(self.request.user)
        if trainer_profile is not None:
            return qs.filter(trainer=trainer_profile)
        return qs.filter(status="ready")

    def perform_create(self, serializer):
        trainer_profile = _trainer_profile_for(self.request.user)
        if trainer_profile is None:
            raise PermissionDenied("Only trainers can create videos.")
        video = CreateVideoService().execute(
            trainer=trainer_profile,
            media_asset_id=serializer.validated_data["media_asset_id"],
            slug=serializer.validated_data["slug"],
            title=serializer.validated_data["title"],
            description=serializer.validated_data.get("description", ""),
            is_free=serializer.validated_data.get("is_free", False),
        )
        serializer.instance = video


class VideoDetailApi(generics.RetrieveUpdateAPIView):
    serializer_class = VideoSerializer
    queryset = Video.objects.filter(is_deleted=False).select_related("trainer", "media_asset")

    def perform_update(self, serializer):
        video = self.get_object()
        trainer_profile = _trainer_profile_for(self.request.user)
        if trainer_profile is None or video.trainer_id != trainer_profile.id:
            raise PermissionDenied("You cannot update this video.")
        serializer.save()


class VideoAccessUrlApi(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, video_id):
        video = get_object_or_404(Video.objects.select_related("media_asset", "trainer"), pk=video_id, is_deleted=False, status="ready")
        payload = IssueVideoAccessUrlService().execute(user=request.user, video=video, request=request)
        return Response(payload)
