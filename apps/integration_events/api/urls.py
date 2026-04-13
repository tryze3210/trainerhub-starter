from rest_framework.routers import DefaultRouter

from .views import (
    AuditLogEntryViewSet,
    DeadLetterEventViewSet,
    DomainOutboxEventViewSet,
    EventSubscriptionViewSet,
    InboundMessageViewSet,
)

router = DefaultRouter()
router.register(r"event-subscriptions", EventSubscriptionViewSet, basename="integration-event-subscription")
router.register(r"outbox-events", DomainOutboxEventViewSet, basename="integration-outbox-event")
router.register(r"dead-letters", DeadLetterEventViewSet, basename="integration-dead-letter")
router.register(r"inbound-messages", InboundMessageViewSet, basename="integration-inbound-message")
router.register(r"audit-log", AuditLogEntryViewSet, basename="integration-audit-log")

urlpatterns = router.urls
