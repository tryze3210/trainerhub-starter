from django.urls import path
from apps.notifications.api.views import (
    AdminNotificationTemplateListCreateView,
    AdminNotificationTemplateDetailView,
    AdminNotificationDeliveryListView,
    AdminNotificationDeliveryOverviewView,
)

urlpatterns = [
    path("admin/templates/", AdminNotificationTemplateListCreateView.as_view(), name="admin-notification-template-list"),
    path("admin/templates/<int:pk>/", AdminNotificationTemplateDetailView.as_view(), name="admin-notification-template-detail"),
    path("admin/deliveries/", AdminNotificationDeliveryListView.as_view(), name="admin-notification-delivery-list"),
    path("admin/deliveries/overview/", AdminNotificationDeliveryOverviewView.as_view(), name="admin-notification-delivery-overview"),
]
