from rest_framework import serializers
from apps.notifications.models import NotificationTemplate, NotificationDelivery


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = ["id", "code", "channel", "subject_template", "body_template", "is_active", "created_at", "updated_at"]


class NotificationDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationDelivery
        fields = [
            "id",
            "channel",
            "type",
            "template_code",
            "subject",
            "status",
            "error_message",
            "provider",
            "provider_message_id",
            "sent_at",
            "created_at",
        ]
