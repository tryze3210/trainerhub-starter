from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from ..models import AuditLogEntry, DeadLetterEvent, DomainOutboxEvent, EventSubscription, InboundMessage
from ..services import EventPublisherService
from .serializers import (
    AuditLogEntrySerializer,
    DeadLetterEventSerializer,
    DomainOutboxEventSerializer,
    EventSubscriptionSerializer,
    InboundMessageSerializer,
)


class EventSubscriptionViewSet(viewsets.ModelViewSet):
    queryset = EventSubscription.objects.all().order_by("code")
    serializer_class = EventSubscriptionSerializer
    permission_classes = [IsAdminUser]


class DomainOutboxEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DomainOutboxEvent.objects.all().order_by("-created_at")
    serializer_class = DomainOutboxEventSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=["post"])
    def replay(self, request, pk=None):
        event = self.get_object()
        result = EventPublisherService.publish_event(event)
        return Response({"delivered": result.delivered, "failed": result.failed}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def dead_letter(self, request, pk=None):
        event = self.get_object()
        reason = request.data.get("reason", "manual dead letter")
        EventPublisherService.dead_letter(event, reason=reason)
        return Response({"status": "dead_lettered"}, status=status.HTTP_200_OK)


class DeadLetterEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DeadLetterEvent.objects.select_related("outbox_event").all().order_by("-created_at")
    serializer_class = DeadLetterEventSerializer
    permission_classes = [IsAdminUser]


class InboundMessageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InboundMessage.objects.all().order_by("-received_at")
    serializer_class = InboundMessageSerializer
    permission_classes = [IsAdminUser]


class AuditLogEntryViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = AuditLogEntry.objects.all().order_by("-created_at")
    serializer_class = AuditLogEntrySerializer
    permission_classes = [IsAdminUser]
