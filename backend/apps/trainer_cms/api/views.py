from django.shortcuts import get_object_or_404
from rest_framework import permissions, response, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.trainer_cms.api.serializers import (
    BundleItemDraftSerializer,
    ProgramLessonDraftSerializer,
    TrainerBundleDraftSerializer,
    TrainerProgramDraftSerializer,
    TrainerVideoDraftSerializer,
)
from apps.trainer_cms.models import (
    BundleItemDraft,
    ProgramLessonDraft,
    TrainerBundleDraft,
    TrainerProgramDraft,
    TrainerVideoDraft,
)
from apps.trainer_cms.business_selectors import TrainerBusinessDashboardSelector
from apps.trainer_cms.selectors import TrainerCMSSelector
from apps.trainer_cms.services import TrainerCMSService
from apps.trainer_profiles.services import ensure_trainer_public_profile
from apps.trainers.models import TrainerApplication
from apps.users.models import User


def _has_approved_trainer_application(user) -> bool:
    application = getattr(user, "trainer_application", None)
    return bool(application and application.status == TrainerApplication.Status.APPROVED)


def _can_access_trainer_cms(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    if getattr(user, "role", None) == User.Roles.TRAINER:
        return True
    return _has_approved_trainer_application(user)


def _trainer_uuid_for_user(user):
    if not _can_access_trainer_cms(user):
        raise PermissionDenied("Trainer CMS is available only after trainer application approval.")
    return ensure_trainer_public_profile(user=user).trainer_uuid


def _raise_validation_error(exc: ValueError):
    raise ValidationError({"detail": str(exc)}) from exc


class TrainerCMSAccessMixin:
    permission_classes = [permissions.IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not _can_access_trainer_cms(request.user):
            raise PermissionDenied("Trainer CMS is available only after trainer application approval.")


class TrainerOwnedMixin(TrainerCMSAccessMixin):
    def perform_create(self, serializer):
        serializer.save(trainer_id=_trainer_uuid_for_user(self.request.user))


class TrainerVideoDraftViewSet(TrainerOwnedMixin, viewsets.ModelViewSet):
    serializer_class = TrainerVideoDraftSerializer
    service = TrainerCMSService()

    def get_queryset(self):
        return TrainerVideoDraft.objects.filter(trainer_id=_trainer_uuid_for_user(self.request.user)).order_by("-created_at")

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        draft = self.get_object()
        try:
            self.service.submit_video_for_review(draft)
        except ValueError as exc:
            _raise_validation_error(exc)
        return response.Response(self.get_serializer(draft).data)

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        draft = self.get_object()
        try:
            self.service.publish_video(draft, actor_id=_trainer_uuid_for_user(request.user))
        except ValueError as exc:
            _raise_validation_error(exc)
        return response.Response(self.get_serializer(draft).data)

    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, pk=None):
        draft = self.get_object()
        self.service.archive_video(draft)
        return response.Response(self.get_serializer(draft).data)


class TrainerProgramDraftViewSet(TrainerOwnedMixin, viewsets.ModelViewSet):
    serializer_class = TrainerProgramDraftSerializer
    service = TrainerCMSService()

    def get_queryset(self):
        return (
            TrainerProgramDraft.objects.filter(trainer_id=_trainer_uuid_for_user(self.request.user))
            .prefetch_related("lessons")
            .order_by("-created_at")
        )

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        draft = self.get_object()
        try:
            self.service.publish_program(draft, actor_id=_trainer_uuid_for_user(request.user))
        except ValueError as exc:
            _raise_validation_error(exc)
        return response.Response(self.get_serializer(draft).data)


class ProgramLessonDraftViewSet(TrainerCMSAccessMixin, viewsets.ModelViewSet):
    serializer_class = ProgramLessonDraftSerializer

    def _program(self):
        return get_object_or_404(
            TrainerProgramDraft,
            id=self.kwargs["program_id"],
            trainer_id=_trainer_uuid_for_user(self.request.user),
        )

    def get_queryset(self):
        return ProgramLessonDraft.objects.filter(program_draft=self._program()).order_by("position", "created_at")

    def perform_create(self, serializer):
        serializer.save(program_draft=self._program())


class TrainerBundleDraftViewSet(TrainerOwnedMixin, viewsets.ModelViewSet):
    serializer_class = TrainerBundleDraftSerializer
    service = TrainerCMSService()

    def get_queryset(self):
        return (
            TrainerBundleDraft.objects.filter(trainer_id=_trainer_uuid_for_user(self.request.user))
            .prefetch_related("items")
            .order_by("-created_at")
        )

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        draft = self.get_object()
        try:
            self.service.publish_bundle(draft, actor_id=_trainer_uuid_for_user(request.user))
        except ValueError as exc:
            _raise_validation_error(exc)
        return response.Response(self.get_serializer(draft).data)


class BundleItemDraftViewSet(TrainerCMSAccessMixin, viewsets.ModelViewSet):
    serializer_class = BundleItemDraftSerializer

    def _bundle(self):
        return get_object_or_404(
            TrainerBundleDraft,
            id=self.kwargs["bundle_id"],
            trainer_id=_trainer_uuid_for_user(self.request.user),
        )

    def get_queryset(self):
        return BundleItemDraft.objects.filter(bundle_draft=self._bundle()).order_by("position", "created_at")

    def perform_create(self, serializer):
        serializer.save(bundle_draft=self._bundle())


class TrainerCMSDashboardViewSet(TrainerCMSAccessMixin, viewsets.ViewSet):
    selector = TrainerCMSSelector()

    def list(self, request):
        return response.Response(self.selector.list_dashboard(_trainer_uuid_for_user(request.user)), status=status.HTTP_200_OK)


class TrainerBusinessDashboardViewSet(TrainerCMSAccessMixin, viewsets.ViewSet):
    selector = TrainerBusinessDashboardSelector()

    def list(self, request):
        try:
            days = int(request.query_params.get("days", 30))
        except (TypeError, ValueError):
            days = 30
        trainer_id = _trainer_uuid_for_user(request.user)
        return response.Response(
            self.selector.build(user=request.user, trainer_id=trainer_id, days=days),
            status=status.HTTP_200_OK,
        )
