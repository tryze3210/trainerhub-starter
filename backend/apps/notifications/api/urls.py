from django.urls import path

from apps.notifications.api.views import (
    AdminAnnouncementDetailView,
    AdminAnnouncementListCreateView,
    AdminAnnouncementPublishView,
    AdminNotificationCenterView,
    AdminNotificationDeliveryListView,
    AdminNotificationDeliveryOverviewView,
    AdminNotificationTemplateDetailView,
    AdminNotificationTemplateListCreateView,
    AdminNotificationProjectionHealthView,
    AdminNotificationProjectOutboxView,
    UserNotificationInboxView,
    UserNotificationMarkAllReadView,
    UserNotificationMarkReadView,
    UserNotificationPreferenceView,
)

urlpatterns = [
    path('inbox/', UserNotificationInboxView.as_view(), name='notification-inbox'),
    path('inbox/mark-all-read/', UserNotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),
    path('inbox/<uuid:notification_id>/read/', UserNotificationMarkReadView.as_view(), name='notification-mark-read'),
    path('preferences/', UserNotificationPreferenceView.as_view(), name='notification-preferences'),
    path('admin/center/', AdminNotificationCenterView.as_view(), name='admin-notification-center'),
    path('admin/announcements/', AdminAnnouncementListCreateView.as_view(), name='admin-announcement-list'),
    path('admin/announcements/<uuid:announcement_id>/', AdminAnnouncementDetailView.as_view(), name='admin-announcement-detail'),
    path('admin/announcements/<uuid:announcement_id>/publish/', AdminAnnouncementPublishView.as_view(), name='admin-announcement-publish'),
    path('admin/templates/', AdminNotificationTemplateListCreateView.as_view(), name='admin-notification-template-list'),
    path('admin/templates/<int:pk>/', AdminNotificationTemplateDetailView.as_view(), name='admin-notification-template-detail'),
    path('admin/deliveries/', AdminNotificationDeliveryListView.as_view(), name='admin-notification-delivery-list'),
    path('admin/deliveries/overview/', AdminNotificationDeliveryOverviewView.as_view(), name='admin-notification-delivery-overview'),
    path('admin/projection-health/', AdminNotificationProjectionHealthView.as_view(), name='admin-notification-projection-health'),
    path('admin/project-outbox/', AdminNotificationProjectOutboxView.as_view(), name='admin-notification-project-outbox'),
]
