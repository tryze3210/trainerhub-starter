from rest_framework.routers import DefaultRouter

from apps.finance.api.views import (
    AdminReconciliationDiscrepancyViewSet,
    AdminReconciliationSessionViewSet,
    AdminSettlementTransactionViewSet,
)

router = DefaultRouter()
router.register(r"admin/finance/settlements", AdminSettlementTransactionViewSet, basename="admin-finance-settlement")
router.register(r"admin/finance/reconciliation/sessions", AdminReconciliationSessionViewSet, basename="admin-finance-reconciliation-session")
router.register(r"admin/finance/reconciliation/discrepancies", AdminReconciliationDiscrepancyViewSet, basename="admin-finance-reconciliation-discrepancy")

urlpatterns = router.urls
