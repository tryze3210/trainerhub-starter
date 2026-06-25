from rest_framework.routers import DefaultRouter

from apps.assignments.api.views import StudentAssignmentViewSet, TrainerAssignmentViewSet, TrainerSubmissionViewSet


router = DefaultRouter()
router.register("student", StudentAssignmentViewSet, basename="assignments-student")
router.register("trainer", TrainerAssignmentViewSet, basename="assignments-trainer")
router.register("trainer/submissions", TrainerSubmissionViewSet, basename="assignments-trainer-submissions")

urlpatterns = router.urls
