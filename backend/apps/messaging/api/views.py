from django.core.exceptions import PermissionDenied, ValidationError
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from apps.access_control.permissions import IsAdminOrSupport
from apps.messaging.models import Conversation, Message, ConversationParticipant
from apps.messaging.api.serializers import (
    ConversationSerializer,
    MessageSerializer,
    SendMessageSerializer,
    StartConversationSerializer,
    SystemMessageSerializer,
)
from apps.messaging.selectors.inbox import conversation_to_dict, get_user_inbox
from apps.messaging.services.conversations import ConversationService


def _error_response(exc):
    status_code = status.HTTP_400_BAD_REQUEST
    if isinstance(exc, PermissionDenied):
        status_code = status.HTTP_403_FORBIDDEN
    detail = getattr(exc, "message", None) or getattr(exc, "messages", None) or str(exc)
    return Response({"detail": detail}, status=status_code)


def _require_participant(*, conversation, user) -> ConversationParticipant:
    try:
        return ConversationParticipant.objects.get(conversation=conversation, user=user)
    except ConversationParticipant.DoesNotExist as exc:
        raise PermissionDenied("Conversation participant required.") from exc


class MyInboxView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        rows = get_user_inbox(request.user)
        return Response({"results": [conversation_to_dict(row) for row in rows], "unread_total": sum(row.unread_count for row in rows)})


class StartConversationView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "messaging_start"

    def post(self, request):
        serializer = StartConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            conversation, message = ConversationService().start_direct_thread(
                sender=request.user,
                recipient_id=serializer.validated_data["recipient_id"],
                subject=serializer.validated_data.get("subject", ""),
                body=serializer.validated_data.get("body", ""),
            )
        except (PermissionDenied, ValidationError) as exc:
            return _error_response(exc)
        participant = ConversationParticipant.objects.get(conversation=conversation, user=request.user)
        payload = conversation_to_dict(participant)
        if message:
            payload["created_message"] = MessageSerializer(message).data
        return Response(payload, status=status.HTTP_201_CREATED)


class ConversationMessagesView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        conversation = get_object_or_404(Conversation, pk=self.kwargs["conversation_id"])
        _require_participant(conversation=conversation, user=self.request.user)
        return conversation.messages.select_related("sender").order_by("created_at")


class SendMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "messaging_send"

    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, pk=conversation_id)
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            message = ConversationService().send_message(
                conversation=conversation,
                sender=request.user,
                body=serializer.validated_data["body"],
            )
        except (PermissionDenied, ValidationError) as exc:
            return _error_response(exc)
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


class MarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, pk=conversation_id)
        participant = _require_participant(conversation=conversation, user=request.user)
        last_message = conversation.messages.order_by("-created_at").first()
        participant.unread_count = 0
        participant.last_read_message_id = getattr(last_message, "id", None)
        participant.save(update_fields=["unread_count", "last_read_message_id"])
        return Response({"status": "ok"})


class CreateSystemMessageView(APIView):
    permission_classes = [IsAdminOrSupport]

    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, pk=conversation_id)
        serializer = SystemMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = ConversationService().create_system_message(
            conversation=conversation,
            body=serializer.validated_data["body"],
            metadata=serializer.validated_data.get("metadata") or {},
        )
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)
