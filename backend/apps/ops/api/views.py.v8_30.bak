from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ops.api.entity_serializers import AdminEntityDetailSerializer
from apps.ops.api.operations_serializers import AdminOperationsDashboardSerializer
from apps.ops.api.reconciliation_serializers import AdminReconciliationQuerySerializer
from apps.ops.api.repair_serializers import AdminReconciliationRepairResultSerializer, AdminReconciliationRepairSerializer
from apps.ops.api.serializers import DiagnosticsSnapshotSerializer, DiagnosticsRunSerializer, RunDiagnosticsSerializer
from apps.ops.api.snapshot_serializers import (
    AdminReconciliationSnapshotCaptureSerializer,
    AdminReconciliationSnapshotListSerializer,
    AdminReconciliationSnapshotTrendSerializer,
)
from apps.ops.entities import AdminEntityNotFound, UnsupportedAdminEntity, get_admin_entity_detail
from apps.ops.operations import get_admin_operations_dashboard
from apps.ops.reconciliation import get_money_reconciliation_report
from apps.ops.reconciliation_snapshots import (
    capture_reconciliation_snapshot,
    get_reconciliation_snapshot_trend,
    list_reconciliation_snapshots,
)
from apps.ops.repair import RepairTargetNotFound, UnsupportedRepairAction, run_reconciliation_repair
from apps.ops.services import DiagnosticsService


class DiagnosticsSnapshotView(APIView):
    service = DiagnosticsService()

    def get(self, request):
        return Response(DiagnosticsSnapshotSerializer(self.service.snapshot()).data)


class RunDiagnosticsView(APIView):
    service = DiagnosticsService()

    def post(self, request):
        serializer = RunDiagnosticsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = self.service.run(**serializer.validated_data)
        return Response({'run': DiagnosticsRunSerializer(payload['run']).data, 'status': payload['status']}, status=status.HTTP_202_ACCEPTED)


class AdminOperationsDashboardView(APIView):
    """Single admin view for money risk, webhook health and outbox health."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        payload = get_admin_operations_dashboard()
        return Response(AdminOperationsDashboardSerializer(payload).data)


class AdminEntityDetailView(APIView):
    """Unified admin detail resolver for operations/audit drill-down pages."""

    permission_classes = [IsAdminUser]

    def get(self, request, entity_type: str, entity_id: str):
        try:
            payload = get_admin_entity_detail(entity_type=entity_type, entity_id=entity_id)
        except AdminEntityNotFound as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except UnsupportedAdminEntity as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(AdminEntityDetailSerializer(payload).data)


class AdminReconciliationReportView(APIView):
    """Read-only reconciliation report for money, access and async pipeline drift."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        serializer = AdminReconciliationQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_money_reconciliation_report(**serializer.validated_data)
        return Response(payload)


class AdminReconciliationRepairView(APIView):
    """Audited repair actions for concrete reconciliation issues."""

    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = AdminReconciliationRepairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            payload = run_reconciliation_repair(
                **serializer.validated_data,
                request=request,
            )
        except RepairTargetNotFound as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except UnsupportedRepairAction as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(AdminReconciliationRepairResultSerializer(payload).data, status=status.HTTP_202_ACCEPTED)


class AdminReconciliationSnapshotListView(APIView):
    """List persisted reconciliation snapshots for trend/history analysis."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        serializer = AdminReconciliationSnapshotListSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = list_reconciliation_snapshots(**serializer.validated_data)
        return Response(payload)


class AdminReconciliationSnapshotCaptureView(APIView):
    """Capture a persisted reconciliation report snapshot on demand."""

    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = AdminReconciliationSnapshotCaptureSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = capture_reconciliation_snapshot(
            **serializer.validated_data,
            request=request,
        )
        return Response(payload, status=status.HTTP_201_CREATED)


class AdminReconciliationSnapshotTrendView(APIView):
    """Trend endpoint for reconciliation issue counts over recent snapshots."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        serializer = AdminReconciliationSnapshotTrendSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_reconciliation_snapshot_trend(**serializer.validated_data)
        return Response(payload)
