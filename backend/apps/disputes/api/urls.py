from django.urls import path

from apps.disputes.api import views

urlpatterns = [
    path("me/", views.MyDisputeListCreateView.as_view(), name="my-disputes"),
    path("me/<uuid:id>/", views.MyDisputeDetailView.as_view(), name="my-dispute-detail"),
    path("admin/overview/", views.AdminDisputeOverviewView.as_view(), name="admin-dispute-overview"),
    path("admin/queue/", views.AdminDisputeQueueView.as_view(), name="admin-dispute-queue"),
    path("admin/cases/<uuid:id>/decision/", views.AdminDisputeDecisionView.as_view(), name="admin-dispute-decision"),
    path("admin/cases/<uuid:id>/refund-review/", views.AdminRefundReviewView.as_view(), name="admin-refund-review"),
]
