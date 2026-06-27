from django.urls import path

from apps.observability.api.views import (
    CorrelationDetailView,
    LogRecordListView,
    MetricListView,
    ObservabilityOverviewView,
    ObservabilityRuntimeView,
    TraceSpanListView,
)

urlpatterns = [
    path('overview/', ObservabilityOverviewView.as_view(), name='observability-overview'),
    path('metrics/', MetricListView.as_view(), name='observability-metrics'),
    path('logs/', LogRecordListView.as_view(), name='observability-logs'),
    path('traces/', TraceSpanListView.as_view(), name='observability-traces'),
    path('correlations/<str:correlation_id>/', CorrelationDetailView.as_view(), name='observability-correlation-detail'),
    path('runtime/', ObservabilityRuntimeView.as_view(), name='observability-runtime'),
]
