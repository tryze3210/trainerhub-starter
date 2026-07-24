from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from apps.access_control.permissions import ROLE_ADMIN, ROLE_TRAINER, user_role_set
from apps.progress.api.serializers import (
    LessonProgressSerializer,
    MarkLessonCompletedSerializer,
    ProgramProgressSerializer,
    SaveVideoProgressSerializer,
    VideoProgressSerializer,
)
from apps.progress.selectors import (
    get_lesson_progress_for_user,
    get_program_progress_for_user,
    get_progress_summary,
    get_trainer_student_progress,
    get_video_progress_for_user,
)
from apps.progress.services import ProgressService


class MyVideoProgressViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VideoProgressSerializer
    throttle_scope = "progress_video_save"

    def get_throttles(self):
        if getattr(self, "action", None) == "save":
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        return get_video_progress_for_user(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='save')
    def save(self, request):
        serializer = SaveVideoProgressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record = ProgressService.save_video_progress(user=request.user, request=request, **serializer.validated_data)
        return Response(VideoProgressSerializer(record).data, status=status.HTTP_200_OK)


class MyLessonProgressViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LessonProgressSerializer
    throttle_scope = "progress_lesson_complete"

    def get_throttles(self):
        if getattr(self, "action", None) == "complete":
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        return get_lesson_progress_for_user(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='complete')
    def complete(self, request):
        serializer = MarkLessonCompletedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record = ProgressService.mark_lesson_completed(user=request.user, request=request, **serializer.validated_data)
        return Response(LessonProgressSerializer(record).data, status=status.HTTP_200_OK)


class MyProgramProgressViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProgramProgressSerializer

    def get_queryset(self):
        return get_program_progress_for_user(user=self.request.user)


class MyProgressSummaryViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        return Response(get_progress_summary(user=request.user))


class TrainerStudentProgressViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        roles = user_role_set(request.user)
        if not roles.intersection({ROLE_TRAINER, ROLE_ADMIN}) and not getattr(request.user, 'is_staff', False):
            return Response({'detail': 'Trainer role required.'}, status=status.HTTP_403_FORBIDDEN)
        return Response(get_trainer_student_progress(trainer_user=request.user))
