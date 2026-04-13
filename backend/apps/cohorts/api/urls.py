from django.urls import path

from apps.cohorts.api import views

urlpatterns = [
    path("me/enrollments/", views.MyCohortEnrollmentsView.as_view(), name="cohorts-my-enrollments"),
    path("me/cohorts/", views.TrainerCohortsView.as_view(), name="cohorts-trainer-list"),
    path("cohorts/<uuid:cohort_id>/dashboard/", views.CohortDashboardView.as_view(), name="cohorts-dashboard"),
    path("admin/cohorts/<uuid:cohort_id>/rebuild-dashboard/", views.RebuildCohortDashboardView.as_view(), name="cohorts-dashboard-rebuild"),
]
