from django.urls import path

from .readiness_views import AdminTrainerApplicationReadinessApi
from .onboarding_views import (
    AdminTrainerApplicationDetailApi,
    AdminTrainerApplicationListApi,
    AdminTrainerApplicationReviewApi,
    AdminTrainerApplicationSyncAccessApi,
    TrainerApplicationStatusApi,
    TrainerOnboardingStateApi,
)
from .views import (
    TrainerApplicationApi,
    TrainerAnalyticsContentApi,
    TrainerAnalyticsOverviewApi,
    TrainerAnalyticsSalesApi,
    TrainerApplicationSubmitApi,
    TrainerCatalogApi,
    TrainerDetailApi,
    TrainerMeProfileApi,
    TrainerRevenuePayoutsApi,
    TrainerRevenueSummaryApi,
    TrainerRevenueTransactionsApi,
)

urlpatterns = [
    path("", TrainerCatalogApi.as_view(), name="trainer-catalog"),
    path("me/application/", TrainerApplicationApi.as_view(), name="trainer-me-application"),
    path("me/application/submit/", TrainerApplicationSubmitApi.as_view(), name="trainer-me-application-submit"),
    path("me/application-status/", TrainerApplicationStatusApi.as_view(), name="trainer-me-application-status"),
    path("me/onboarding/status/", TrainerOnboardingStateApi.as_view(), name="trainer-me-onboarding-status"),
    path("me/profile/", TrainerMeProfileApi.as_view(), name="trainer-me-profile"),
    path("me/analytics/overview/", TrainerAnalyticsOverviewApi.as_view(), name="trainer-me-analytics-overview"),
    path("me/analytics/content/", TrainerAnalyticsContentApi.as_view(), name="trainer-me-analytics-content"),
    path("me/analytics/sales/", TrainerAnalyticsSalesApi.as_view(), name="trainer-me-analytics-sales"),
    path("me/revenue/summary/", TrainerRevenueSummaryApi.as_view(), name="trainer-me-revenue-summary"),
    path("me/revenue/transactions/", TrainerRevenueTransactionsApi.as_view(), name="trainer-me-revenue-transactions"),
    path("me/revenue/payouts/", TrainerRevenuePayoutsApi.as_view(), name="trainer-me-revenue-payouts"),
    path("admin/applications/", AdminTrainerApplicationListApi.as_view(), name="trainer-admin-application-list"),
    path("admin/applications/readiness/", AdminTrainerApplicationReadinessApi.as_view(), name="trainer-admin-application-readiness"),
    path(
        "admin/applications/<uuid:application_id>/",
        AdminTrainerApplicationDetailApi.as_view(),
        name="trainer-admin-application-detail",
    ),
    path(
        "admin/applications/<uuid:application_id>/review/",
        AdminTrainerApplicationReviewApi.as_view(),
        name="trainer-admin-application-review",
    ),
    path(
        "admin/applications/<uuid:application_id>/sync-access/",
        AdminTrainerApplicationSyncAccessApi.as_view(),
        name="trainer-admin-application-sync-access",
    ),
    path("<slug:slug>/", TrainerDetailApi.as_view(), name="trainer-detail"),
]
