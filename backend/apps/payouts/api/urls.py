from rest_framework.routers import DefaultRouter

from apps.payouts.api.views import AdminPayoutViewSet, MyPayoutViewSet

router = DefaultRouter()
router.register(r'my', MyPayoutViewSet, basename='my-payouts')
router.register(r'admin', AdminPayoutViewSet, basename='admin-payouts')

urlpatterns = router.urls
