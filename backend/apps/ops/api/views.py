from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ops.api.entity_serializers import AdminEntityDetailSerializer
from apps.ops.api.operations_serializers import (
    AdminCommerceReadinessQuerySerializer,
    AdminCommerceReadinessSerializer,
    AdminOperationsDashboardSerializer,
    AdminOperationsHubQuerySerializer,
    AdminOperationsHubSerializer,
    AdminOperationsReadinessQuerySerializer,
    AdminOperationsReadinessSerializer,
    AdminProductionReadinessQuerySerializer,
    AdminProductionReadinessSerializer,
)
from apps.ops.api.reconciliation_serializers import AdminReconciliationQuerySerializer
from apps.ops.api.repair_serializers import (
    AdminReconciliationRepairPolicySerializer,
    AdminReconciliationRepairResultSerializer,
    AdminReconciliationRepairSerializer,
)
from apps.ops.api.serializers import DiagnosticsRunSerializer, DiagnosticsSnapshotSerializer, RunDiagnosticsSerializer
from apps.ops.api.snapshot_serializers import (
    AdminReconciliationIssueRegistrySerializer,
    AdminReconciliationSnapshotAlertSerializer,
    AdminReconciliationSnapshotCaptureSerializer,
    AdminReconciliationSnapshotCompareSerializer,
    AdminReconciliationSnapshotLatestSerializer,
    AdminReconciliationSnapshotListSerializer,
    AdminReconciliationSnapshotMetricsSerializer,
    AdminReconciliationSnapshotRetentionSerializer,
    AdminReconciliationSnapshotScheduleSerializer,
    AdminReconciliationSnapshotTrendSerializer,
)
from apps.ops.entities import AdminEntityNotFound, UnsupportedAdminEntity, get_admin_entity_detail
from apps.ops.operations import get_admin_operations_dashboard
from apps.ops.commerce_readiness import get_commerce_readiness
from apps.ops.operations_hub import get_admin_operations_hub
from apps.ops.operations_readiness import get_ops_production_readiness
from apps.ops.payment_reconciliation import get_payment_reconciliation_report
from apps.ops.production_readiness import get_platform_production_readiness
from apps.ops.reconciliation import get_money_reconciliation_report
from apps.ops.reconciliation_snapshots import (
    capture_reconciliation_snapshot,
    compare_reconciliation_snapshots,
    get_latest_reconciliation_snapshot,
    get_reconciliation_issue_registry,
    get_reconciliation_snapshot_metrics,
    get_reconciliation_snapshot_alerts,
    get_reconciliation_snapshot_retention_policy,
    get_reconciliation_snapshot_schedule,
    get_reconciliation_snapshot_trend,
    list_reconciliation_snapshots,
    notify_reconciliation_snapshot_alerts,
)
from apps.ops.repair import (
    RepairTargetNotFound,
    UnsupportedRepairAction,
    get_reconciliation_repair_policy,
    run_reconciliation_repair,
)
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
        return Response(
            {'run': DiagnosticsRunSerializer(payload['run']).data, 'status': payload['status']},
            status=status.HTTP_202_ACCEPTED,
        )


class AdminOperationsDashboardView(APIView):
    """Single admin view for money risk, webhook health and outbox health."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        payload = get_admin_operations_dashboard()
        return Response(AdminOperationsDashboardSerializer(payload).data)




class AdminOperationsHubView(APIView):
    """Unified admin operations command center for async infra, money risk and reconciliation."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        serializer = AdminOperationsHubQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_admin_operations_hub(**serializer.validated_data)
        return Response(AdminOperationsHubSerializer(payload).data)


class AdminCommerceReadinessView(APIView):
    """Read-only commerce readiness report for trainer monetization and public storefront surfaces."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        serializer = AdminCommerceReadinessQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_commerce_readiness(**serializer.validated_data)
        return Response(AdminCommerceReadinessSerializer(payload).data)


class AdminOperationsReadinessView(APIView):
    """Read-only production readiness report for the ops/reconciliation surface."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        serializer = AdminOperationsReadinessQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_ops_production_readiness(**serializer.validated_data)
        return Response(AdminOperationsReadinessSerializer(payload).data)


class AdminProductionReadinessView(APIView):
    """Read-only v95 production readiness gate for the full platform surface."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        serializer = AdminProductionReadinessQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_platform_production_readiness(**serializer.validated_data)
        return Response(AdminProductionReadinessSerializer(payload).data)


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


class AdminPaymentReconciliationView(APIView):
    """Read-only payment reconciliation across provider webhooks, internal payments and access grants."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        serializer = AdminReconciliationQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_payment_reconciliation_report(**serializer.validated_data)
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


class AdminReconciliationRepairPolicyView(APIView):
    """Return workflow/risk metadata for a reconciliation repair action before execution."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        serializer = AdminReconciliationRepairPolicySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        try:
            payload = get_reconciliation_repair_policy(**serializer.validated_data)
        except UnsupportedRepairAction as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(payload)


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


class AdminReconciliationSnapshotLatestView(APIView):
    """Return the latest reconciliation snapshot, optionally filtered by source."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        serializer = AdminReconciliationSnapshotLatestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_latest_reconciliation_snapshot(**serializer.validated_data)
        return Response(payload)


class AdminReconciliationSnapshotTrendView(APIView):
    """Trend endpoint for reconciliation issue counts over recent snapshots."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        serializer = AdminReconciliationSnapshotTrendSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_reconciliation_snapshot_trend(**serializer.validated_data)
        return Response(payload)


class AdminReconciliationSnapshotMetricsView(APIView):
    """Compact dashboard metrics for reconciliation snapshot health and repair effectiveness."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        serializer = AdminReconciliationSnapshotMetricsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_reconciliation_snapshot_metrics(**serializer.validated_data)
        return Response(payload)


class AdminReconciliationSnapshotAlertView(APIView):
    """Evaluate and optionally emit reconciliation snapshot alerts for admins."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        serializer = AdminReconciliationSnapshotAlertSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        data.pop('notify_admins', None)
        data.pop('dedupe_hours', None)
        payload = get_reconciliation_snapshot_alerts(**data)
        return Response(payload)

    def post(self, request):
        serializer = AdminReconciliationSnapshotAlertSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        payload = notify_reconciliation_snapshot_alerts(
            **serializer.validated_data,
            request=request,
        )
        return Response(payload, status=status.HTTP_202_ACCEPTED)


class AdminReconciliationSnapshotRetentionView(APIView):
    """Preview or execute reconciliation snapshot retention pruning."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        serializer = AdminReconciliationSnapshotRetentionSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_reconciliation_snapshot_retention_policy(
            **serializer.validated_data,
            execute=False,
        )
        return Response(payload)

    def post(self, request):
        serializer = AdminReconciliationSnapshotRetentionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = get_reconciliation_snapshot_retention_policy(
            **serializer.validated_data,
            execute=True,
        )
        return Response(payload, status=status.HTTP_200_OK)


class AdminReconciliationSnapshotScheduleView(APIView):
    """Read scheduled reconciliation snapshot freshness state for ops dashboard/beat checks."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        serializer = AdminReconciliationSnapshotScheduleSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_reconciliation_snapshot_schedule(**serializer.validated_data)
        return Response(payload)


class AdminReconciliationIssueRegistryView(APIView):
    """Return normalized reconciliation issues from the latest or selected snapshot."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        serializer = AdminReconciliationIssueRegistrySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_reconciliation_issue_registry(**serializer.validated_data)
        return Response(payload)


class AdminReconciliationSnapshotCompareView(APIView):
    """Compare two reconciliation snapshots and expose resolved/introduced issue diffs."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        serializer = AdminReconciliationSnapshotCompareSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = compare_reconciliation_snapshots(**serializer.validated_data)
        return Response(payload)
