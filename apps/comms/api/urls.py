from rest_framework.routers import DefaultRouter

from apps.comms.api.views import (
    AdminCommunicationLedgerViewSet,
    AdminDeliveryAttemptViewSet,
    AdminNotificationMessageViewSet,
    AdminNotificationTemplateViewSet,
    AdminSuppressionRuleViewSet,
    UserNotificationPreferenceViewSet,
)

router = DefaultRouter()
router.register(r"admin/templates", AdminNotificationTemplateViewSet, basename="admin-comms-template")
router.register(r"preferences", UserNotificationPreferenceViewSet, basename="user-comms-preference")
router.register(r"admin/suppression-rules", AdminSuppressionRuleViewSet, basename="admin-comms-suppression-rule")
router.register(r"admin/messages", AdminNotificationMessageViewSet, basename="admin-comms-message")
router.register(r"admin/delivery-attempts", AdminDeliveryAttemptViewSet, basename="admin-comms-delivery-attempt")
router.register(r"admin/ledger", AdminCommunicationLedgerViewSet, basename="admin-comms-ledger")

urlpatterns = router.urls
