from rest_framework import serializers
from apps.audit.models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = ['id', 'actor', 'event_type', 'entity_type', 'entity_id', 'context', 'ip_address', 'user_agent', 'created_at']
