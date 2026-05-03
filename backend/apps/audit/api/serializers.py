from __future__ import annotations

from rest_framework import serializers

from apps.audit.models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    actor_email = serializers.SerializerMethodField()

    class Meta:
        model = AuditEvent
        fields = [
            'id',
            'actor',
            'actor_email',
            'event_type',
            'entity_type',
            'entity_id',
            'context',
            'ip_address',
            'user_agent',
            'created_at',
            'updated_at',
        ]

    def get_actor_email(self, obj: AuditEvent) -> str:
        return getattr(obj.actor, 'email', '') if obj.actor_id else ''
