from rest_framework.routers import DefaultRouter

from apps.audit.api.views import AuditAdminViewSet

router = DefaultRouter()
router.register(r"admin/events", AuditAdminViewSet, basename="admin-audit-events")

urlpatterns = router.urls
