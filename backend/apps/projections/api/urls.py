from django.urls import path

from apps.projections.api.views import ProjectionRebuildView, ProjectionStatusListView

urlpatterns = [
    path('statuses/', ProjectionStatusListView.as_view(), name='projection-statuses'),
    path('rebuild/', ProjectionRebuildView.as_view(), name='projection-rebuild'),
]
