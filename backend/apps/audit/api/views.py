from rest_framework import mixins, viewsets
from apps.audit.api.serializers import AuditEventSerializer
from apps.audit.models import AuditEvent
from apps.common.api.permissions import IsAdminUserRole


class AuditAdminViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAdminUserRole]
    serializer_class = AuditEventSerializer
    queryset = AuditEvent.objects.all().order_by('-created_at')
