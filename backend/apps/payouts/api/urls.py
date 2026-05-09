from __future__ import annotations

from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.payouts.api.readiness_views import AdminPayoutReadinessAPIView
from apps.payouts.api.views import AdminPayoutViewSet, MyPayoutViewSet

router = DefaultRouter()
router.register(r"my", MyPayoutViewSet, basename="my-payouts")
router.register(r"admin", AdminPayoutViewSet, basename="admin-payouts")

urlpatterns = [
    # Keep this before router.urls so "admin/readiness" is not captured as
    # AdminPayoutViewSet detail pk="readiness".
    path("admin/readiness/", AdminPayoutReadinessAPIView.as_view(), name="admin-payout-readiness"),
    *router.urls,
]
