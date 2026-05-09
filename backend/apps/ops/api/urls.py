from django.urls import path

from apps.ops.api.views import (
    AdminCommerceReadinessView,
    AdminEntityDetailView,
    AdminOperationsDashboardView,
    AdminOperationsHubView,
    AdminOperationsReadinessView,
    AdminReconciliationIssueRegistryView,
    AdminReconciliationReportView,
    AdminReconciliationRepairPolicyView,
    AdminReconciliationRepairView,
    AdminReconciliationSnapshotAlertView,
    AdminReconciliationSnapshotCaptureView,
    AdminReconciliationSnapshotCompareView,
    AdminReconciliationSnapshotLatestView,
    AdminReconciliationSnapshotListView,
    AdminReconciliationSnapshotMetricsView,
    AdminReconciliationSnapshotRetentionView,
    AdminReconciliationSnapshotScheduleView,
    AdminReconciliationSnapshotTrendView,
    DiagnosticsSnapshotView,
    RunDiagnosticsView,
)

urlpatterns = [
    path('diagnostics/', DiagnosticsSnapshotView.as_view(), name='ops-diagnostics'),
    path('diagnostics/run/', RunDiagnosticsView.as_view(), name='ops-diagnostics-run'),
    path('admin/operations-dashboard/', AdminOperationsDashboardView.as_view(), name='ops-admin-operations-dashboard'),
    path('admin/operations-hub/', AdminOperationsHubView.as_view(), name='ops-admin-operations-hub'),
    path('admin/operations-readiness/', AdminOperationsReadinessView.as_view(), name='ops-admin-operations-readiness'),
    path('admin/commerce-readiness/', AdminCommerceReadinessView.as_view(), name='ops-admin-commerce-readiness'),
    path('admin/reconciliation-report/', AdminReconciliationReportView.as_view(), name='ops-admin-reconciliation-report'),
    path('admin/reconciliation-repair/', AdminReconciliationRepairView.as_view(), name='ops-admin-reconciliation-repair'),
    path(
        'admin/reconciliation-repair/policy/',
        AdminReconciliationRepairPolicyView.as_view(),
        name='ops-admin-reconciliation-repair-policy',
    ),
    path('admin/reconciliation-snapshots/', AdminReconciliationSnapshotListView.as_view(), name='ops-admin-reconciliation-snapshots'),
    path(
        'admin/reconciliation-snapshots/capture/',
        AdminReconciliationSnapshotCaptureView.as_view(),
        name='ops-admin-reconciliation-snapshot-capture',
    ),
    path(
        'admin/reconciliation-snapshots/latest/',
        AdminReconciliationSnapshotLatestView.as_view(),
        name='ops-admin-reconciliation-snapshot-latest',
    ),
    path(
        'admin/reconciliation-snapshots/trend/',
        AdminReconciliationSnapshotTrendView.as_view(),
        name='ops-admin-reconciliation-snapshot-trend',
    ),
    path(
        'admin/reconciliation-snapshots/metrics/',
        AdminReconciliationSnapshotMetricsView.as_view(),
        name='ops-admin-reconciliation-snapshot-metrics',
    ),

    path(
        'admin/reconciliation-snapshots/alerts/',
        AdminReconciliationSnapshotAlertView.as_view(),
        name='ops-admin-reconciliation-snapshot-alerts',
    ),

    path(
        'admin/reconciliation-snapshots/retention/',
        AdminReconciliationSnapshotRetentionView.as_view(),
        name='ops-admin-reconciliation-snapshot-retention',
    ),

    path(
        'admin/reconciliation-snapshots/schedule/',
        AdminReconciliationSnapshotScheduleView.as_view(),
        name='ops-admin-reconciliation-snapshot-schedule',
    ),

    path(
        'admin/reconciliation-snapshots/issues/',
        AdminReconciliationIssueRegistryView.as_view(),
        name='ops-admin-reconciliation-snapshot-issues',
    ),
    path(
        'admin/reconciliation-snapshots/compare/',
        AdminReconciliationSnapshotCompareView.as_view(),
        name='ops-admin-reconciliation-snapshot-compare',
    ),
    path('admin/entities/<str:entity_type>/<str:entity_id>/', AdminEntityDetailView.as_view(), name='ops-admin-entity-detail'),
]
