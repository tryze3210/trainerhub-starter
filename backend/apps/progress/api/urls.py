from rest_framework.routers import DefaultRouter

from apps.progress.api.views import (
    MyLessonProgressViewSet,
    MyProgramProgressViewSet,
    MyProgressSummaryViewSet,
    MyVideoProgressViewSet,
    TrainerStudentProgressViewSet,
)


router = DefaultRouter()
router.register("videos", MyVideoProgressViewSet, basename="progress-videos")
router.register("lessons", MyLessonProgressViewSet, basename="progress-lessons")
router.register("programs", MyProgramProgressViewSet, basename="progress-programs")
router.register("summary", MyProgressSummaryViewSet, basename="progress-summary")
router.register("trainer/students", TrainerStudentProgressViewSet, basename="progress-trainer-students")

urlpatterns = router.urls
