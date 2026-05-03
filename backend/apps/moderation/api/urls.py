from django.urls import path

from apps.moderation.api import views

urlpatterns = [
    path("admin/overview/", views.AdminModerationOverviewView.as_view()),
    path("admin/queue/", views.AdminModerationQueueView.as_view()),
    path("admin/maintenance/", views.AdminMarketplaceCoreMaintenanceView.as_view()),
    path("admin/cases/<uuid:case_id>/", views.AdminModerationCaseDetailView.as_view()),
    path("admin/cases/<uuid:case_id>/assign/", views.AdminModerationCaseAssignView.as_view()),
    path("admin/cases/<uuid:case_id>/decision/", views.AdminModerationDecisionCreateView.as_view()),
    path("admin/risk-dashboard/", views.AdminPaymentRiskDashboardView.as_view()),
    path("admin/payment-risk-cases/", views.AdminPaymentRiskCasesView.as_view()),
    path("admin/payment-risk/project-outbox/", views.AdminPaymentRiskProjectOutboxView.as_view()),
    path("admin/risk-flags/", views.AdminTrainerRiskFlagsView.as_view()),
    path("admin/risk-flags/create/", views.AdminTrainerRiskFlagCreateView.as_view()),
    path("admin/risk-flags/<uuid:flag_id>/resolve/", views.AdminTrainerRiskFlagResolveView.as_view()),
    path("me/status/", views.TrainerModerationStatusView.as_view()),
]
