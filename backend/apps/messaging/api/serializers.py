from rest_framework import serializers
from apps.messaging.models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    sender_email = serializers.SerializerMethodField()

    def get_sender_email(self, obj):
        return getattr(obj.sender, "email", "") if obj.sender_id else "System"

    class Meta:
        model = Message
        fields = ["id", "conversation", "sender", "sender_email", "message_type", "body", "delivery_status", "metadata", "created_at"]


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ["id", "kind", "booking_reservation_id", "trainer_id", "client_id", "subject", "last_message_at", "created_at", "updated_at"]


class StartConversationSerializer(serializers.Serializer):
    recipient_id = serializers.UUIDField()
    subject = serializers.CharField(required=False, allow_blank=True, max_length=255)
    body = serializers.CharField(required=False, allow_blank=True)


class SendMessageSerializer(serializers.Serializer):
    body = serializers.CharField()


class SystemMessageSerializer(serializers.Serializer):
    body = serializers.CharField()
    metadata = serializers.JSONField(required=False)
