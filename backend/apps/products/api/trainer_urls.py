from rest_framework.routers import DefaultRouter

from apps.products.api.trainer_views import TrainerProductBuilderViewSet

router = DefaultRouter()
router.register("trainer", TrainerProductBuilderViewSet, basename="trainer-products")

urlpatterns = router.urls
