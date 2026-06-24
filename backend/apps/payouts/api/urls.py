from __future__ import annotations

from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.payouts.api.ops_views import (
    AdminPayoutOpsIntegrityAPIView,
    AdminPayoutOpsLedgerExportAPIView,
    AdminPayoutOpsReconciliationReportExportCsvAPIView,
    AdminPayoutOpsReconciliationReportExportXlsxAPIView,
    AdminPayoutOpsReconciliationSnapshotAPIView,
    AdminPayoutOpsRepairAuditExportCsvAPIView,
    AdminPayoutOpsRepairAuditExportXlsxAPIView,
    AdminPayoutOpsRepairPreviewAPIView,
    AdminPayoutOpsRequestsExportAPIView,
    AdminPayoutOpsSummaryAPIView,
)
from apps.payouts.api.readiness_views import AdminPayoutReadinessAPIView
from apps.payouts.api.repair_execution_views import AdminPayoutOpsRepairExecuteAPIView
from apps.payouts.api.views import AdminPayoutViewSet, MyPayoutViewSet

router = DefaultRouter()
router.register(r"my", MyPayoutViewSet, basename="my-payouts")
router.register(r"admin", AdminPayoutViewSet, basename="admin-payouts")

urlpatterns = [
    # Keep fixed admin paths before router.urls so they are not captured as detail pk values.
    path("admin/readiness/", AdminPayoutReadinessAPIView.as_view(), name="admin-payout-readiness"),
    path("admin-ops/summary/", AdminPayoutOpsSummaryAPIView.as_view(), name="admin-payout-ops-summary"),
    path(
        "admin-ops/reconciliation/snapshot/",
        AdminPayoutOpsReconciliationSnapshotAPIView.as_view(),
        name="admin-payout-ops-reconciliation-snapshot",
    ),
    path(
        "admin-ops/integrity/",
        AdminPayoutOpsIntegrityAPIView.as_view(),
        name="admin-payout-ops-integrity",
    ),
    path(
        "admin-ops/repair/preview/",
        AdminPayoutOpsRepairPreviewAPIView.as_view(),
        name="admin-payout-ops-repair-preview",
    ),
    path(
        "admin-ops/repair/execute/",
        AdminPayoutOpsRepairExecuteAPIView.as_view(),
        name="admin-payout-ops-repair-execute",
    ),
    path(
        "admin-ops/repair/audit/export.csv",
        AdminPayoutOpsRepairAuditExportCsvAPIView.as_view(),
        name="admin-payout-ops-repair-audit-export-csv",
    ),
    path(
        "admin-ops/repair/audit/export.xlsx",
        AdminPayoutOpsRepairAuditExportXlsxAPIView.as_view(),
        name="admin-payout-ops-repair-audit-export-xlsx",
    ),
    path(
        "admin-ops/reconciliation/export.csv",
        AdminPayoutOpsReconciliationReportExportCsvAPIView.as_view(),
        name="admin-payout-ops-reconciliation-report-export-csv",
    ),
    path(
        "admin-ops/reconciliation/export.xlsx",
        AdminPayoutOpsReconciliationReportExportXlsxAPIView.as_view(),
        name="admin-payout-ops-reconciliation-report-export-xlsx",
    ),
    path(
        "admin-ops/requests/export.csv",
        AdminPayoutOpsRequestsExportAPIView.as_view(),
        name="admin-payout-ops-requests-export",
    ),
    path(
        "admin-ops/ledger/export.csv",
        AdminPayoutOpsLedgerExportAPIView.as_view(),
        name="admin-payout-ops-ledger-export",
    ),
    *router.urls,
]
