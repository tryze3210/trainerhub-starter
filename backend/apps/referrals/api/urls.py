from django.urls import path

from apps.referrals.api.admin_views import (
    AdminReferralAttributionListView,
    AdminReferralInviteDetailView,
    AdminReferralInviteExportView,
    AdminReferralInviteListView,
    AdminReferralLedgerExportView,
    AdminReferralLedgerListView,
    AdminReferralOpsOverviewView,
    AdminReferralRewardDetailView,
    AdminReferralRewardExportView,
    AdminReferralRewardListView,
)
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
    path("admin/ops/overview/", AdminReferralOpsOverviewView.as_view(), name="referrals-admin-ops-overview"),
    path("admin/rewards/", AdminReferralRewardListView.as_view(), name="referrals-admin-rewards"),
    path("admin/rewards/export.csv", AdminReferralRewardExportView.as_view(), name="referrals-admin-rewards-export"),
    path("admin/rewards/<uuid:pk>/", AdminReferralRewardDetailView.as_view(), name="referrals-admin-reward-detail"),
    path("admin/ledger/", AdminReferralLedgerListView.as_view(), name="referrals-admin-ledger"),
    path("admin/ledger/export.csv", AdminReferralLedgerExportView.as_view(), name="referrals-admin-ledger-export"),
    path("admin/invites/", AdminReferralInviteListView.as_view(), name="referrals-admin-invites"),
    path("admin/invites/export.csv", AdminReferralInviteExportView.as_view(), name="referrals-admin-invites-export"),
    path("admin/invites/<uuid:pk>/", AdminReferralInviteDetailView.as_view(), name="referrals-admin-invite-detail"),
    path("admin/attributions/", AdminReferralAttributionListView.as_view(), name="referrals-admin-attributions"),
]
