from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from apps.comms.api.serializers import (
    CommunicationLedgerSerializer,
    DeliveryAttemptSerializer,
    NotificationMessageSerializer,
    NotificationPreferenceSerializer,
    NotificationTemplateSerializer,
    SuppressionRuleSerializer,
)
from apps.comms.models import (
    CommunicationLedger,
    DeliveryAttempt,
    NotificationMessage,
    NotificationPreference,
    NotificationTemplate,
    SuppressionRule,
)


class AdminNotificationTemplateViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser,)
    queryset = NotificationTemplate.objects.all().order_by("key", "channel", "locale")
    serializer_class = NotificationTemplateSerializer


class UserNotificationPreferenceViewSet(
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (IsAuthenticated,)
    serializer_class = NotificationPreferenceSerializer

    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user).order_by("category", "channel")


class AdminSuppressionRuleViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser,)
    queryset = SuppressionRule.objects.all().order_by("code")
    serializer_class = SuppressionRuleSerializer


class AdminNotificationMessageViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAdminUser,)
    queryset = NotificationMessage.objects.all().order_by("-created_at")
    serializer_class = NotificationMessageSerializer


class AdminDeliveryAttemptViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAdminUser,)
    queryset = DeliveryAttempt.objects.select_related("message").all().order_by("-attempted_at")
    serializer_class = DeliveryAttemptSerializer


class AdminCommunicationLedgerViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAdminUser,)
    queryset = CommunicationLedger.objects.select_related("message", "user").all().order_by("-occurred_at")
    serializer_class = CommunicationLedgerSerializer
