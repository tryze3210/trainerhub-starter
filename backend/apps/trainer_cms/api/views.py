from rest_framework import permissions, response, status, viewsets
from rest_framework.decorators import action
from apps.trainer_cms.api.serializers import TrainerBundleDraftSerializer, TrainerProgramDraftSerializer, TrainerVideoDraftSerializer
from apps.trainer_cms.models import TrainerBundleDraft, TrainerProgramDraft, TrainerVideoDraft
from apps.trainer_cms.selectors import TrainerCMSSelector
from apps.trainer_cms.services import TrainerCMSService
from apps.trainer_profiles.services import ensure_trainer_public_profile


def _trainer_uuid_for_user(user):
    return ensure_trainer_public_profile(user=user).trainer_uuid


class TrainerOwnedMixin:
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(trainer_id=_trainer_uuid_for_user(self.request.user))


class TrainerVideoDraftViewSet(TrainerOwnedMixin, viewsets.ModelViewSet):
    serializer_class = TrainerVideoDraftSerializer
    service = TrainerCMSService()

    def get_queryset(self):
        return TrainerVideoDraft.objects.filter(trainer_id=_trainer_uuid_for_user(self.request.user)).order_by('-created_at')

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        draft = self.get_object()
        self.service.submit_video_for_review(draft)
        return response.Response(self.get_serializer(draft).data)

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        draft = self.get_object()
        self.service.publish_video(draft, actor_id=_trainer_uuid_for_user(request.user))
        return response.Response(self.get_serializer(draft).data)

    @action(detail=True, methods=['post'], url_path='archive')
    def archive(self, request, pk=None):
        draft = self.get_object()
        self.service.archive_video(draft)
        return response.Response(self.get_serializer(draft).data)


class TrainerProgramDraftViewSet(TrainerOwnedMixin, viewsets.ModelViewSet):
    serializer_class = TrainerProgramDraftSerializer
    service = TrainerCMSService()

    def get_queryset(self):
        return TrainerProgramDraft.objects.filter(trainer_id=_trainer_uuid_for_user(self.request.user)).order_by('-created_at')

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        draft = self.get_object()
        self.service.publish_program(draft, actor_id=_trainer_uuid_for_user(request.user))
        return response.Response(self.get_serializer(draft).data)


class TrainerBundleDraftViewSet(TrainerOwnedMixin, viewsets.ModelViewSet):
    serializer_class = TrainerBundleDraftSerializer
    service = TrainerCMSService()

    def get_queryset(self):
        return TrainerBundleDraft.objects.filter(trainer_id=_trainer_uuid_for_user(self.request.user)).order_by('-created_at')

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        draft = self.get_object()
        self.service.publish_bundle(draft, actor_id=_trainer_uuid_for_user(request.user))
        return response.Response(self.get_serializer(draft).data)


class TrainerCMSDashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    selector = TrainerCMSSelector()

    def list(self, request):
        return response.Response(self.selector.list_dashboard(_trainer_uuid_for_user(request.user)), status=status.HTTP_200_OK)
