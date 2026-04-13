from datetime import datetime

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from apps.finance_reporting.api.serializers import (
    FinanceReconciliationSnapshotSerializer,
    SettlementReportSerializer,
)
from apps.finance_reporting.models import FinanceReconciliationSnapshot, SettlementReport
from apps.finance_reporting.services.exporters import settlement_report_to_csv, settlement_report_to_xlsx
from apps.finance_reporting.services.reconciliation import FinanceReconciliationService


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class SettlementReportViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SettlementReportSerializer
    permission_classes = [IsAdminUser]
    queryset = SettlementReport.objects.prefetch_related("lines").all()

    @action(detail=False, methods=["post"], url_path="build")
    def build(self, request):
        period_start = datetime.fromisoformat(request.data["period_start"]).date()
        period_end = datetime.fromisoformat(request.data["period_end"]).date()
        report = FinanceReconciliationService().build_settlement_report(period_start, period_end)
        return Response(self.get_serializer(report).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="finalize")
    def finalize(self, request, pk=None):
        report = self.get_object()
        report.status = SettlementReport.STATUS_FINALIZED
        report.finalized_at = timezone.now()
        report.save(update_fields=["status", "finalized_at"])
        return Response(self.get_serializer(report).data)

    @action(detail=True, methods=["get"], url_path="export/csv")
    def export_csv(self, request, pk=None):
        report = self.get_object()
        report.export_count += 1
        report.status = SettlementReport.STATUS_EXPORTED
        report.save(update_fields=["export_count", "status"])
        response = HttpResponse(settlement_report_to_csv(report), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="settlement_{report.period_start}_{report.period_end}.csv"'
        return response

    @action(detail=True, methods=["get"], url_path="export/xlsx")
    def export_xlsx(self, request, pk=None):
        report = self.get_object()
        report.export_count += 1
        report.status = SettlementReport.STATUS_EXPORTED
        report.save(update_fields=["export_count", "status"])
        response = HttpResponse(settlement_report_to_xlsx(report), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="settlement_{report.period_start}_{report.period_end}.xlsx"'
        return response


@api_view(["GET"])
@permission_classes([IsAdminUser])
def reconciliation_overview(request):
    days = int(request.GET.get("days", 30))
    snapshots = FinanceReconciliationSnapshot.objects.all()[:days]
    latest = FinanceReconciliationSnapshot.objects.first()
    return Response({
        "latest": FinanceReconciliationSnapshotSerializer(latest).data if latest else None,
        "timeseries": FinanceReconciliationSnapshotSerializer(snapshots, many=True).data,
    })


@api_view(["POST"])
@permission_classes([IsAdminUser])
def refresh_reconciliation(request):
    days = int(request.data.get("days", 30))
    FinanceReconciliationService().bootstrap_recent_snapshots(days=days)
    latest = FinanceReconciliationSnapshot.objects.first()
    return Response(FinanceReconciliationSnapshotSerializer(latest).data if latest else {})
