from rest_framework.routers import DefaultRouter
from apps.content.api.views import PublishedBundleViewSet, PublishedProgramViewSet, PublishedVideoViewSet

router = DefaultRouter()
router.register('videos', PublishedVideoViewSet, basename='published-videos')
router.register('programs', PublishedProgramViewSet, basename='published-programs')
router.register('bundles', PublishedBundleViewSet, basename='published-bundles')

urlpatterns = router.urls
