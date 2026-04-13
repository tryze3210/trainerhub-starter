from rest_framework.routers import DefaultRouter

from finance_closing.api.views import (
    AccountingDocumentAdminViewSet,
    ClosingPeriodAdminViewSet,
    FinanceCloseAuditLogAdminViewSet,
    FinanceSnapshotAdminViewSet,
    TrainerMonthStatementAdminViewSet,
)

router = DefaultRouter()
router.register('admin/finance/periods', ClosingPeriodAdminViewSet, basename='finance-period')
router.register('admin/finance/snapshots', FinanceSnapshotAdminViewSet, basename='finance-snapshot')
router.register('admin/finance/statements', TrainerMonthStatementAdminViewSet, basename='trainer-statement')
router.register('admin/finance/documents', AccountingDocumentAdminViewSet, basename='finance-document')
router.register('admin/finance/audit-log', FinanceCloseAuditLogAdminViewSet, basename='finance-audit-log')

urlpatterns = router.urls
