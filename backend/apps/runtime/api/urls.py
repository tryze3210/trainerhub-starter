from django.urls import path

from apps.runtime.api.views import CachePingView, RuntimeConfigView, RuntimeHealthView, RuntimeReadinessView

urlpatterns = [
    path('health/', RuntimeHealthView.as_view(), name='runtime-health'),
    path('readiness/', RuntimeReadinessView.as_view(), name='runtime-readiness'),
    path('config/', RuntimeConfigView.as_view(), name='runtime-config'),
    path('cache/ping/', CachePingView.as_view(), name='runtime-cache-ping'),
]
