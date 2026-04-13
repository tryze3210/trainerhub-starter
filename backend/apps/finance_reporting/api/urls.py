from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.finance_reporting.api.views import (
    SettlementReportViewSet,
    reconciliation_overview,
    refresh_reconciliation,
)

router = DefaultRouter()
router.register("settlements", SettlementReportViewSet, basename="finance-settlements")

urlpatterns = [
    path("admin/overview/", reconciliation_overview, name="finance-reconciliation-overview"),
    path("admin/refresh/", refresh_reconciliation, name="finance-reconciliation-refresh"),
    path("admin/", include(router.urls)),
]
