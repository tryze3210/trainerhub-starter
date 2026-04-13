from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from apps.messaging.models import Conversation, Message, ConversationParticipant
from apps.messaging.api.serializers import ConversationSerializer, MessageSerializer
from apps.messaging.selectors.inbox import get_user_inbox


class MyInboxView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        rows = get_user_inbox(request.user)
        data = []
        for row in rows:
            payload = ConversationSerializer(row.conversation).data
            payload["unread_count"] = row.unread_count
            data.append(payload)
        return Response(data)


class ConversationMessagesView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        conversation = get_object_or_404(Conversation, pk=self.kwargs["conversation_id"])
        ConversationParticipant.objects.get(conversation=conversation, user=self.request.user)
        return conversation.messages.select_related("sender").order_by("created_at")


class SendMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, pk=conversation_id)
        ConversationParticipant.objects.get(conversation=conversation, user=request.user)
        body = request.data.get("body", "").strip()
        if not body:
            return Response({"detail": "body is required"}, status=status.HTTP_400_BAD_REQUEST)
        message = Message.objects.create(conversation=conversation, sender=request.user, body=body)
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


class MarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, pk=conversation_id)
        participant = get_object_or_404(ConversationParticipant, conversation=conversation, user=request.user)
        last_message = conversation.messages.order_by("-created_at").first()
        participant.unread_count = 0
        participant.last_read_message_id = getattr(last_message, "id", None)
        participant.save(update_fields=["unread_count", "last_read_message_id"])
        return Response({"status": "ok"})
