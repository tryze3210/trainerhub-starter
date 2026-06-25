from rest_framework.routers import DefaultRouter
from django.urls import path
from apps.content.api.views import (
    CourseLessonRuntimeApi,
    ProgramLessonRuntimeApi,
    PublishedBundleViewSet,
    PublishedProgramViewSet,
    PublishedVideoViewSet,
    StudentLearningAreaApi,
)

router = DefaultRouter()
router.register('videos', PublishedVideoViewSet, basename='published-videos')
router.register('programs', PublishedProgramViewSet, basename='published-programs')
router.register('bundles', PublishedBundleViewSet, basename='published-bundles')

urlpatterns = [
    path("student/learning-area/", StudentLearningAreaApi.as_view(), name="content-student-learning-area"),
    path(
        "runtime/programs/<slug:program_slug>/lessons/<slug:lesson_ref>/",
        ProgramLessonRuntimeApi.as_view(),
        name="content-runtime-program-lesson",
    ),
    path(
        "runtime/courses/<uuid:course_id>/lessons/<uuid:lesson_id>/",
        CourseLessonRuntimeApi.as_view(),
        name="content-runtime-course-lesson",
    ),
] + router.urls
