from django.urls import path

from apps.reviews.api.views import (
    AdminPendingReviewListView,
    AdminReviewModerationView,
    AdminReviewTrustCenterView,
    TrainerReviewReplyView,
    TargetReviewsView,
    TrainerReviewQualityView,
)

urlpatterns = [
    path('admin/trust-center/', AdminReviewTrustCenterView.as_view(), name='reviews-admin-trust-center'),
    path('admin/pending/', AdminPendingReviewListView.as_view(), name='reviews-admin-pending'),
    path('admin/<str:review_id>/moderate/', AdminReviewModerationView.as_view(), name='reviews-admin-moderate'),
    path('trainer/quality/', TrainerReviewQualityView.as_view(), name='reviews-trainer-quality'),
    path('trainer/<str:review_id>/reply/', TrainerReviewReplyView.as_view(), name='reviews-trainer-reply'),
    path('<str:target_type>/<str:target_id>/', TargetReviewsView.as_view(), name='target-reviews'),
]
