from django.urls import path
from rest_framework.routers import DefaultRouter
from apps.trainer_cms.api.views import (
    BundleItemDraftViewSet,
    ProgramLessonDraftViewSet,
    TrainerBundleDraftViewSet,
    TrainerBusinessDashboardViewSet,
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
    path("business-dashboard/", TrainerBusinessDashboardViewSet.as_view({"get": "list"}), name="trainer-business-dashboard"),
    path(
        "programs/<uuid:program_id>/lessons/",
        ProgramLessonDraftViewSet.as_view({"get": "list", "post": "create"}),
        name="trainer-program-lessons-list",
    ),
    path(
        "programs/<uuid:program_id>/lessons/<uuid:pk>/",
        ProgramLessonDraftViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="trainer-program-lessons-detail",
    ),
    path(
        "bundles/<uuid:bundle_id>/items/",
        BundleItemDraftViewSet.as_view({"get": "list", "post": "create"}),
        name="trainer-bundle-items-list",
    ),
    path(
        "bundles/<uuid:bundle_id>/items/<uuid:pk>/",
        BundleItemDraftViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="trainer-bundle-items-detail",
    ),
]
