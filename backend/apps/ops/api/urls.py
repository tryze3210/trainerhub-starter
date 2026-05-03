from django.urls import path

from apps.ops.api.views import (
    AdminEntityDetailView,
    AdminOperationsDashboardView,
    AdminReconciliationReportView,
    AdminReconciliationRepairView,
    AdminReconciliationSnapshotCaptureView,
    AdminReconciliationSnapshotListView,
    AdminReconciliationSnapshotTrendView,
    DiagnosticsSnapshotView,
    RunDiagnosticsView,
)

urlpatterns = [
    path('diagnostics/', DiagnosticsSnapshotView.as_view(), name='ops-diagnostics'),
    path('diagnostics/run/', RunDiagnosticsView.as_view(), name='ops-diagnostics-run'),
    path('admin/operations-dashboard/', AdminOperationsDashboardView.as_view(), name='ops-admin-operations-dashboard'),
    path('admin/reconciliation-report/', AdminReconciliationReportView.as_view(), name='ops-admin-reconciliation-report'),
    path('admin/reconciliation-repair/', AdminReconciliationRepairView.as_view(), name='ops-admin-reconciliation-repair'),
    path('admin/reconciliation-snapshots/', AdminReconciliationSnapshotListView.as_view(), name='ops-admin-reconciliation-snapshots'),
    path('admin/reconciliation-snapshots/capture/', AdminReconciliationSnapshotCaptureView.as_view(), name='ops-admin-reconciliation-snapshot-capture'),
    path('admin/reconciliation-snapshots/trend/', AdminReconciliationSnapshotTrendView.as_view(), name='ops-admin-reconciliation-snapshot-trend'),
    path('admin/entities/<str:entity_type>/<str:entity_id>/', AdminEntityDetailView.as_view(), name='ops-admin-entity-detail'),
]
