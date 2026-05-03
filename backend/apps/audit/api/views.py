from __future__ import annotations

from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAdminUser

from apps.audit.api.serializers import AuditEventSerializer
from apps.audit.models import AuditEvent


class AuditAdminViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Admin-only audit feed for operator actions and support investigations."""

    permission_classes = [IsAdminUser]
    serializer_class = AuditEventSerializer

    def get_queryset(self):
        queryset = AuditEvent.objects.select_related('actor').all().order_by('-created_at')
        event_type = (self.request.query_params.get('event_type') or '').strip()
        entity_type = (self.request.query_params.get('entity_type') or '').strip()
        entity_id = (self.request.query_params.get('entity_id') or '').strip()
        actor_id = (self.request.query_params.get('actor_id') or '').strip()
        limit_raw = (self.request.query_params.get('limit') or '').strip()

        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        if entity_id:
            queryset = queryset.filter(entity_id=entity_id)
        if actor_id:
            queryset = queryset.filter(actor_id=actor_id)
        if limit_raw:
            try:
                queryset = queryset[: max(1, min(int(limit_raw), 500))]
            except ValueError:
                queryset = queryset[:100]
        return queryset
