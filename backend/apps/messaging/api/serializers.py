from rest_framework import serializers
from apps.messaging.models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "conversation", "sender", "body", "delivery_status", "created_at"]


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ["id", "kind", "booking_reservation_id", "subject", "last_message_at", "created_at"]
