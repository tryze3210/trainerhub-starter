from rest_framework import serializers

from ..models import AuditLogEntry, DeadLetterEvent, DomainOutboxEvent, EventSubscription, InboundMessage


class EventSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventSubscription
        fields = "__all__"


class DomainOutboxEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = DomainOutboxEvent
        fields = "__all__"


class DeadLetterEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeadLetterEvent
        fields = "__all__"


class InboundMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = InboundMessage
        fields = "__all__"


class AuditLogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLogEntry
        fields = "__all__"
