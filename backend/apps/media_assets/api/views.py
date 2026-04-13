from rest_framework import permissions, response, status, viewsets
from rest_framework.decorators import action
from apps.media_assets.api.serializers import CreateUploadSessionSerializer, MediaAssetSerializer
from apps.media_assets.models import MediaAsset
from apps.media_assets.services import MediaAssetService
from apps.trainer_profiles.services import ensure_trainer_public_profile


class MediaAssetViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MediaAssetSerializer
    service = MediaAssetService()

    def _trainer_uuid(self):
        return ensure_trainer_public_profile(user=self.request.user).trainer_uuid

    def get_queryset(self):
        return MediaAsset.objects.filter(trainer_id=self._trainer_uuid()).order_by('-created_at')

    def list(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return response.Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='upload-session')
    def upload_session(self, request):
        serializer = CreateUploadSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = self.service.create_upload_session(trainer_id=self._trainer_uuid(), **serializer.validated_data)
        return response.Response(payload, status=status.HTTP_201_CREATED)
