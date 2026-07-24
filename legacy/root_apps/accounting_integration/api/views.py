from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from apps.accounting_integration.api.serializers import (
    AccountMappingRuleSerializer,
    ChartOfAccountSerializer,
    ExternalAccountingSystemSerializer,
    GLExportRunSerializer,
    JournalBatchSerializer,
)
from apps.accounting_integration.models import (
    AccountMappingRule,
    ChartOfAccount,
    ExternalAccountingSystem,
    GLExportRun,
    JournalBatch,
)
from apps.accounting_integration.services import GLExportService


class ExternalAccountingSystemViewSet(viewsets.ModelViewSet):
    queryset = ExternalAccountingSystem.objects.all().order_by("name")
    serializer_class = ExternalAccountingSystemSerializer
    permission_classes = [IsAdminUser]


class ChartOfAccountViewSet(viewsets.ModelViewSet):
    queryset = ChartOfAccount.objects.select_related("system").all().order_by("system_id", "code")
    serializer_class = ChartOfAccountSerializer
    permission_classes = [IsAdminUser]


class AccountMappingRuleViewSet(viewsets.ModelViewSet):
    queryset = AccountMappingRule.objects.select_related("system", "account").all().order_by("system_id", "target_type", "source_code")
    serializer_class = AccountMappingRuleSerializer
    permission_classes = [IsAdminUser]


class JournalBatchViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = JournalBatch.objects.select_related("system", "period", "snapshot", "created_by").all().order_by("-created_at")
    serializer_class = JournalBatchSerializer
    permission_classes = [IsAdminUser]


class GLExportRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GLExportRun.objects.select_related("system", "period", "journal_batch", "created_by").all().order_by("-created_at")
    serializer_class = GLExportRunSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=["post"])
    def queue(self, request, pk=None):
        export_run = self.get_object()
        GLExportService().queue_export(export_run=export_run)
        return Response(self.get_serializer(export_run).data)

    @action(detail=True, methods=["post"])
    def render(self, request, pk=None):
        export_run = self.get_object()
        GLExportService().render_export_payload(export_run=export_run)
        return Response(self.get_serializer(export_run).data)

    @action(detail=True, methods=["post"])
    def deliver(self, request, pk=None):
        export_run = self.get_object()
        GLExportService().deliver_export(export_run=export_run)
        return Response(self.get_serializer(export_run).data)
