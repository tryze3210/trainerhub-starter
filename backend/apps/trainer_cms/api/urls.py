from django.urls import path
from rest_framework.routers import DefaultRouter
from apps.trainer_cms.api.views import (
    TrainerBundleDraftViewSet,
    TrainerCMSDashboardViewSet,
    TrainerProgramDraftViewSet,
    TrainerVideoDraftViewSet,
)

router = DefaultRouter()
router.register("videos", TrainerVideoDraftViewSet, basename="trainer-video-drafts")
router.register("programs", TrainerProgramDraftViewSet, basename="trainer-program-drafts")
router.register("bundles", TrainerBundleDraftViewSet, basename="trainer-bundle-drafts")

urlpatterns = router.urls + [
    path("dashboard/", TrainerCMSDashboardViewSet.as_view({"get": "list"}), name="trainer-cms-dashboard"),
]
