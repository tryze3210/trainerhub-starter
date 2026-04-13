from django.urls import path

from apps.reviews.api.views import TargetReviewsView

urlpatterns = [
    path('<str:target_type>/<str:target_id>/', TargetReviewsView.as_view(), name='target-reviews'),
]
