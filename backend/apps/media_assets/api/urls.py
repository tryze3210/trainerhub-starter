from rest_framework.routers import DefaultRouter
from apps.media_assets.api.views import MediaAssetViewSet

router = DefaultRouter()
router.register("assets", MediaAssetViewSet, basename="media-assets")

urlpatterns = router.urls
