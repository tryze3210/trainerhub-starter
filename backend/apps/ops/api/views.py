from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.access_control.permissions import IsAdminOrSupport, IsAdminSupportFinanceReadonly
from apps.notifications.models import NotificationDelivery
from apps.ops.api.entity_serializers import AdminEntityDetailSerializer
from apps.ops.api.operations_serializers import (
    AdminCommerceReadinessQuerySerializer,
    AdminCommerceReadinessSerializer,
    AdminGlobalSearchQuerySerializer,
    AdminGlobalSearchSerializer,
    AdminLaunchCandidateQuerySerializer,
    AdminLaunchCandidateSerializer,
    AdminOperationsDashboardSerializer,
    AdminOperationsHubQuerySerializer,
    AdminOperationsHubSerializer,
    AdminOperationsReadinessQuerySerializer,
    AdminOperationsReadinessSerializer,
    AdminOpsRunbookDetailSerializer,
    AdminOpsRunbookIndexSerializer,
    AdminOpsRunbookQuerySerializer,
    AdminProductionLaunchPackQuerySerializer,
    AdminProductionLaunchPackSerializer,
    AdminProductionReadinessQuerySerializer,
    AdminProductionReadinessSerializer,
    SupportConsoleQuerySerializer,
    SupportConsoleSnapshotSerializer,
    SupportEntitlementFixSerializer,
    SupportNotificationResendSerializer,
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
from apps.ops.admin_global_search import get_admin_global_search, parse_categories
from apps.ops.operations import get_admin_operations_dashboard
from apps.ops.support_console import (
    SupportConsoleAccessDenied,
    SupportConsoleTargetNotFound,
    fix_entitlement,
    get_support_console_snapshot,
    resend_notification_delivery,
)
from apps.ops.commerce_readiness import get_commerce_readiness
from apps.ops.launch_candidate import get_launch_candidate_pack
from apps.ops.operations_hub import get_admin_operations_hub
from apps.ops.operations_readiness import get_ops_production_readiness
from apps.ops.payment_reconciliation import get_payment_reconciliation_report
from apps.ops.production_launch_pack import get_production_launch_pack
from apps.ops.production_readiness import get_platform_production_readiness
from apps.ops.reconciliation import get_money_reconciliation_report
from apps.ops.runbooks import get_ops_runbook, get_ops_runbook_index
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
from apps.observability.api.serializers import ObservabilityRuntimeQuerySerializer, ObservabilityRuntimeSnapshotSerializer
from apps.observability.runtime import get_observability_runtime_snapshot


class AdminOpsThrottledAPIView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'admin_ops'


class DiagnosticsSnapshotView(AdminOpsThrottledAPIView):
    permission_classes = [IsAdminSupportFinanceReadonly]
    service = DiagnosticsService()

    def get(self, request):
        return Response(DiagnosticsSnapshotSerializer(self.service.snapshot()).data)


class RunDiagnosticsView(AdminOpsThrottledAPIView):
    permission_classes = [IsAdminSupportFinanceReadonly]
    service = DiagnosticsService()

    def post(self, request):
        serializer = RunDiagnosticsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = self.service.run(**serializer.validated_data)
        return Response(
            {'run': DiagnosticsRunSerializer(payload['run']).data, 'status': payload['status']},
            status=status.HTTP_202_ACCEPTED,
        )


class AdminOperationsDashboardView(AdminOpsThrottledAPIView):
    """Single admin view for money risk, webhook health and outbox health."""

    permission_classes = [IsAdminSupportFinanceReadonly]

    def get(self, request):
        payload = get_admin_operations_dashboard()
        return Response(AdminOperationsDashboardSerializer(payload).data)




class AdminOperationsHubView(AdminOpsThrottledAPIView):
    """Unified admin operations command center for async infra, money risk and reconciliation."""

    permission_classes = [IsAdminSupportFinanceReadonly]

    def get(self, request):
        serializer = AdminOperationsHubQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_admin_operations_hub(**serializer.validated_data)
        return Response(AdminOperationsHubSerializer(payload).data)


class AdminCommerceReadinessView(AdminOpsThrottledAPIView):
    """Read-only commerce readiness report for trainer monetization and public storefront surfaces."""

    permission_classes = [IsAdminSupportFinanceReadonly]

    def get(self, request):
        serializer = AdminCommerceReadinessQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_commerce_readiness(**serializer.validated_data)
        return Response(AdminCommerceReadinessSerializer(payload).data)


class AdminOperationsReadinessView(AdminOpsThrottledAPIView):
    """Read-only production readiness report for the ops/reconciliation surface."""

    permission_classes = [IsAdminSupportFinanceReadonly]

    def get(self, request):
        serializer = AdminOperationsReadinessQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_ops_production_readiness(**serializer.validated_data)
        return Response(AdminOperationsReadinessSerializer(payload).data)


class AdminObservabilityRuntimeView(AdminOpsThrottledAPIView):
    """Production observability snapshot for webhooks, payments, payout repairs and background jobs."""

    permission_classes = [IsAdminSupportFinanceReadonly]

    def get(self, request):
        serializer = ObservabilityRuntimeQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_observability_runtime_snapshot(**serializer.validated_data)
        return Response(ObservabilityRuntimeSnapshotSerializer(payload).data)


class AdminProductionReadinessView(AdminOpsThrottledAPIView):
    """Read-only v95 production readiness gate for the full platform surface."""

    permission_classes = [IsAdminSupportFinanceReadonly]

    def get(self, request):
        serializer = AdminProductionReadinessQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_platform_production_readiness(**serializer.validated_data)
        return Response(AdminProductionReadinessSerializer(payload).data)


class AdminLaunchCandidateView(AdminOpsThrottledAPIView):
    """Read-only v119 launch candidate pack with release notes and launch checklists."""

    permission_classes = [IsAdminSupportFinanceReadonly]

    def get(self, request):
        serializer = AdminLaunchCandidateQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_launch_candidate_pack(**serializer.validated_data)
        return Response(AdminLaunchCandidateSerializer(payload).data)


class AdminProductionLaunchPackView(AdminOpsThrottledAPIView):
    """Read-only v120 production launch documentation and handoff pack."""

    permission_classes = [IsAdminSupportFinanceReadonly]

    def get(self, request):
        serializer = AdminProductionLaunchPackQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_production_launch_pack(**serializer.validated_data)
        return Response(AdminProductionLaunchPackSerializer(payload).data)


class AdminOpsRunbookIndexView(AdminOpsThrottledAPIView):
    permission_classes = [IsAdminSupportFinanceReadonly]

    def get(self, request):
        serializer = AdminOpsRunbookQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_ops_runbook_index(**serializer.validated_data)
        return Response(AdminOpsRunbookIndexSerializer(payload).data)


class AdminOpsRunbookDetailView(AdminOpsThrottledAPIView):
    permission_classes = [IsAdminSupportFinanceReadonly]

    def get(self, request, key: str):
        try:
            payload = get_ops_runbook(key=key)
        except KeyError:
            return Response({"detail": "Runbook was not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(AdminOpsRunbookDetailSerializer(payload).data)


class AdminEntityDetailView(AdminOpsThrottledAPIView):
    """Unified admin detail resolver for operations/audit drill-down pages."""

    permission_classes = [IsAdminSupportFinanceReadonly]

    def get(self, request, entity_type: str, entity_id: str):
        try:
            payload = get_admin_entity_detail(entity_type=entity_type, entity_id=entity_id)
        except AdminEntityNotFound as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except UnsupportedAdminEntity as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(AdminEntityDetailSerializer(payload).data)


class AdminGlobalSearchView(AdminOpsThrottledAPIView):
    """Tenant-aware global search across core admin entities."""

    permission_classes = [IsAdminSupportFinanceReadonly]

    def get(self, request):
        serializer = AdminGlobalSearchQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_admin_global_search(
            user=request.user,
            query=serializer.validated_data["q"],
            categories=parse_categories(serializer.validated_data.get("categories")),
            limit=serializer.validated_data["limit"],
        )
        return Response(AdminGlobalSearchSerializer(payload).data)


class SupportConsoleView(AdminOpsThrottledAPIView):
    """Support operator console for user commerce/access investigations."""

    permission_classes = [IsAdminOrSupport]

    def get(self, request):
        serializer = SupportConsoleQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        try:
            payload = get_support_console_snapshot(operator=request.user, **serializer.validated_data)
        except SupportConsoleTargetNotFound as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except SupportConsoleAccessDenied as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        return Response(SupportConsoleSnapshotSerializer(payload).data)


class SupportNotificationResendView(AdminOpsThrottledAPIView):
    permission_classes = [IsAdminOrSupport]

    def post(self, request):
        serializer = SupportNotificationResendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            payload = resend_notification_delivery(
                operator=request.user,
                request=request,
                **serializer.validated_data,
            )
        except NotificationDelivery.DoesNotExist:
            return Response({"detail": "Notification delivery was not found."}, status=status.HTTP_404_NOT_FOUND)
        except SupportConsoleAccessDenied as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        return Response(payload, status=status.HTTP_202_ACCEPTED)


class SupportEntitlementFixView(AdminOpsThrottledAPIView):
    permission_classes = [IsAdminOrSupport]

    def post(self, request):
        serializer = SupportEntitlementFixSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            payload = fix_entitlement(
                operator=request.user,
                request=request,
                **serializer.validated_data,
            )
        except SupportConsoleTargetNotFound as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except SupportConsoleAccessDenied as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(payload, status=status.HTTP_202_ACCEPTED)


class AdminReconciliationReportView(AdminOpsThrottledAPIView):
    """Read-only reconciliation report for money, access and async pipeline drift."""

    permission_classes = [IsAdminSupportFinanceReadonly]

    def get(self, request):
        serializer = AdminReconciliationQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_money_reconciliation_report(**serializer.validated_data)
        return Response(payload)


class AdminPaymentReconciliationView(AdminOpsThrottledAPIView):
    """Read-only payment reconciliation across provider webhooks, internal payments and access grants."""

    permission_classes = [IsAdminSupportFinanceReadonly]

    def get(self, request):
        serializer = AdminReconciliationQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_payment_reconciliation_report(**serializer.validated_data)
        return Response(payload)


class AdminReconciliationRepairView(AdminOpsThrottledAPIView):
    """Audited repair actions for concrete reconciliation issues."""

    permission_classes = [IsAdminSupportFinanceReadonly]

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


class AdminReconciliationRepairPolicyView(AdminOpsThrottledAPIView):
    """Return workflow/risk metadata for a reconciliation repair action before execution."""

    permission_classes = [IsAdminSupportFinanceReadonly]

    def get(self, request):
        serializer = AdminReconciliationRepairPolicySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        try:
            payload = get_reconciliation_repair_policy(**serializer.validated_data)
        except UnsupportedRepairAction as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(payload)


class AdminReconciliationSnapshotListView(AdminOpsThrottledAPIView):
    """List persisted reconciliation snapshots for trend/history analysis."""

    permission_classes = [IsAdminSupportFinanceReadonly]

    def get(self, request):
        serializer = AdminReconciliationSnapshotListSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = list_reconciliation_snapshots(**serializer.validated_data)
        return Response(payload)


class AdminReconciliationSnapshotCaptureView(AdminOpsThrottledAPIView):
    """Capture a persisted reconciliation report snapshot on demand."""

    permission_classes = [IsAdminSupportFinanceReadonly]

    def post(self, request):
        serializer = AdminReconciliationSnapshotCaptureSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = capture_reconciliation_snapshot(
            **serializer.validated_data,
            request=request,
        )
        return Response(payload, status=status.HTTP_201_CREATED)


class AdminReconciliationSnapshotLatestView(AdminOpsThrottledAPIView):
    """Return the latest reconciliation snapshot, optionally filtered by source."""

    permission_classes = [IsAdminSupportFinanceReadonly]

    def get(self, request):
        serializer = AdminReconciliationSnapshotLatestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_latest_reconciliation_snapshot(**serializer.validated_data)
        return Response(payload)


class AdminReconciliationSnapshotTrendView(AdminOpsThrottledAPIView):
    """Trend endpoint for reconciliation issue counts over recent snapshots."""

    permission_classes = [IsAdminSupportFinanceReadonly]

    def get(self, request):
        serializer = AdminReconciliationSnapshotTrendSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_reconciliation_snapshot_trend(**serializer.validated_data)
        return Response(payload)


class AdminReconciliationSnapshotMetricsView(AdminOpsThrottledAPIView):
    """Compact dashboard metrics for reconciliation snapshot health and repair effectiveness."""

    permission_classes = [IsAdminSupportFinanceReadonly]

    def get(self, request):
        serializer = AdminReconciliationSnapshotMetricsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_reconciliation_snapshot_metrics(**serializer.validated_data)
        return Response(payload)


class AdminReconciliationSnapshotAlertView(AdminOpsThrottledAPIView):
    """Evaluate and optionally emit reconciliation snapshot alerts for admins."""

    permission_classes = [IsAdminSupportFinanceReadonly]

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


class AdminReconciliationSnapshotRetentionView(AdminOpsThrottledAPIView):
    """Preview or execute reconciliation snapshot retention pruning."""

    permission_classes = [IsAdminSupportFinanceReadonly]

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


class AdminReconciliationSnapshotScheduleView(AdminOpsThrottledAPIView):
    """Read scheduled reconciliation snapshot freshness state for ops dashboard/beat checks."""

    permission_classes = [IsAdminSupportFinanceReadonly]

    def get(self, request):
        serializer = AdminReconciliationSnapshotScheduleSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_reconciliation_snapshot_schedule(**serializer.validated_data)
        return Response(payload)


class AdminReconciliationIssueRegistryView(AdminOpsThrottledAPIView):
    """Return normalized reconciliation issues from the latest or selected snapshot."""

    permission_classes = [IsAdminSupportFinanceReadonly]

    def get(self, request):
        serializer = AdminReconciliationIssueRegistrySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_reconciliation_issue_registry(**serializer.validated_data)
        return Response(payload)


class AdminReconciliationSnapshotCompareView(AdminOpsThrottledAPIView):
    """Compare two reconciliation snapshots and expose resolved/introduced issue diffs."""

    permission_classes = [IsAdminSupportFinanceReadonly]

    def get(self, request):
        serializer = AdminReconciliationSnapshotCompareSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = compare_reconciliation_snapshots(**serializer.validated_data)
        return Response(payload)
