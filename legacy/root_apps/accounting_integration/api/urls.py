from rest_framework.routers import DefaultRouter

from apps.accounting_integration.api.views import (
    AccountMappingRuleViewSet,
    ChartOfAccountViewSet,
    ExternalAccountingSystemViewSet,
    GLExportRunViewSet,
    JournalBatchViewSet,
)

router = DefaultRouter()
router.register(r"external-systems", ExternalAccountingSystemViewSet, basename="external-accounting-system")
router.register(r"chart-of-accounts", ChartOfAccountViewSet, basename="chart-of-account")
router.register(r"mapping-rules", AccountMappingRuleViewSet, basename="account-mapping-rule")
router.register(r"journal-batches", JournalBatchViewSet, basename="journal-batch")
router.register(r"gl-export-runs", GLExportRunViewSet, basename="gl-export-run")

urlpatterns = router.urls
