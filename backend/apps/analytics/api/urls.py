from django.urls import path

from apps.analytics.api.views import (
    AnalyticsEventCollectView,
    AnalyticsProjectionHealthView,
    AnalyticsProjectOutboxView,
    FunnelTimeSeriesView,
    KPIOverviewView,
    RetentionCohortsView,
    RevenueTimeSeriesView,
    TopTrainersView,
    TrafficAttributionView,
    TrafficTimeSeriesView,
    TrafficTopPathsView,
    TrainerRevenueDashboardView,
    WarehouseHealthView,
)


urlpatterns = [
    path('events/collect/', AnalyticsEventCollectView.as_view(), name='analytics-event-collect'),
    path('events/projection-health/', AnalyticsProjectionHealthView.as_view(), name='analytics-events-projection-health'),
    path('events/project-outbox/', AnalyticsProjectOutboxView.as_view(), name='analytics-events-project-outbox'),
    path('overview/', KPIOverviewView.as_view(), name='admin-analytics-overview'),
    path('revenue-timeseries/', RevenueTimeSeriesView.as_view(), name='admin-analytics-revenue-timeseries'),
    path('top-trainers/', TopTrainersView.as_view(), name='admin-analytics-top-trainers'),
    path('funnel-timeseries/', FunnelTimeSeriesView.as_view(), name='admin-analytics-funnel-timeseries'),
    path('retention-cohorts/', RetentionCohortsView.as_view(), name='admin-analytics-retention-cohorts'),
    path('warehouse-health/', WarehouseHealthView.as_view(), name='admin-analytics-warehouse-health'),
    path('traffic-timeseries/', TrafficTimeSeriesView.as_view(), name='admin-analytics-traffic-timeseries'),
    path('traffic-top-paths/', TrafficTopPathsView.as_view(), name='admin-analytics-traffic-top-paths'),
    path('traffic-attribution/', TrafficAttributionView.as_view(), name='admin-analytics-traffic-attribution'),
    path('trainer-dashboard/', TrainerRevenueDashboardView.as_view(), name='trainer-analytics-dashboard'),
]
