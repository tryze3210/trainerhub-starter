from django.urls import path

from apps.referrals.api.views import (
    AdminOverviewView,
    GenerateCodeView,
    MyDashboardView,
    MyInvitesView,
    MyProgramView,
    MyRewardsView,
    TrackReferralView,
)

urlpatterns = [
    path("me/program/", MyProgramView.as_view(), name="referrals-me-program"),
    path("me/dashboard/", MyDashboardView.as_view(), name="referrals-me-dashboard"),
    path("me/generate-code/", GenerateCodeView.as_view(), name="referrals-generate-code"),
    path("me/invites/", MyInvitesView.as_view(), name="referrals-me-invites"),
    path("me/rewards/", MyRewardsView.as_view(), name="referrals-me-rewards"),
    path("track/", TrackReferralView.as_view(), name="referrals-track"),
    path("admin/overview/", AdminOverviewView.as_view(), name="referrals-admin-overview"),
]
