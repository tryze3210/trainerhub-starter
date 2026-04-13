from rest_framework.routers import DefaultRouter

from apps.billing.api.views import PayoutBatchAdminViewSet, TrainerLedgerViewSet, TrainerRevenuePolicyAdminViewSet

router = DefaultRouter()
router.register("admin/revenue-policies", TrainerRevenuePolicyAdminViewSet, basename="billing-admin-revenue-policy")
router.register("trainer/ledger", TrainerLedgerViewSet, basename="billing-trainer-ledger")
router.register("admin/payout-batches", PayoutBatchAdminViewSet, basename="billing-admin-payout-batch")

urlpatterns = router.urls
