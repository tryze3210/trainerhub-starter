from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.events.api.serializers import EmitEventSerializer, InboxMessageSerializer, OutboxMessageSerializer
from apps.events.services import DomainEventService


class OutboxMessageListView(APIView):
    service = DomainEventService()

    def get(self, request):
        return Response(OutboxMessageSerializer(self.service.list_outbox(), many=True).data)


class InboxMessageListView(APIView):
    service = DomainEventService()

    def get(self, request):
        return Response(InboxMessageSerializer(self.service.list_inbox(), many=True).data)


class EmitEventView(APIView):
    service = DomainEventService()

    def post(self, request):
        serializer = EmitEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = self.service.emit(**serializer.validated_data)
        return Response(payload, status=status.HTTP_202_ACCEPTED)
