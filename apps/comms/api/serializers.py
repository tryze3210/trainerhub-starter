from rest_framework import serializers

from apps.comms.models import (
    CommunicationLedger,
    DeliveryAttempt,
    NotificationMessage,
    NotificationPreference,
    NotificationTemplate,
    SuppressionRule,
)


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = "__all__"


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = "__all__"
        read_only_fields = ("user",)


class SuppressionRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuppressionRule
        fields = "__all__"


class NotificationMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationMessage
        fields = "__all__"


class DeliveryAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryAttempt
        fields = "__all__"


class CommunicationLedgerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunicationLedger
        fields = "__all__"
