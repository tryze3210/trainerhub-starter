from django.urls import path

from apps.access_control.api.views import AccessSnapshotView, FeatureCheckView, ObjectCheckView

urlpatterns = [
    path('snapshot/', AccessSnapshotView.as_view(), name='access-snapshot'),
    path('check-feature/', FeatureCheckView.as_view(), name='access-check-feature'),
    path('check-object/', ObjectCheckView.as_view(), name='access-check-object'),
]
