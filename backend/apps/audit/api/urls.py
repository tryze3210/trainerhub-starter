from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.audit.api.views import (
    AuditAdminCsvExportView,
    AuditAdminRetentionCleanupView,
    AuditAdminRetentionPreviewView,
    AuditAdminRetentionSummaryView,
    AuditAdminViewSet,
)

router = DefaultRouter()
router.register(r'admin/events', AuditAdminViewSet, basename='admin-audit-events')

urlpatterns = [
    path('admin/events/export.csv', AuditAdminCsvExportView.as_view(), name='admin-audit-events-export'),
    path('admin/retention/summary/', AuditAdminRetentionSummaryView.as_view(), name='admin-audit-retention-summary'),
    path('admin/retention/preview/', AuditAdminRetentionPreviewView.as_view(), name='admin-audit-retention-preview'),
    path('admin/retention/cleanup/', AuditAdminRetentionCleanupView.as_view(), name='admin-audit-retention-cleanup'),
    *router.urls,
]
