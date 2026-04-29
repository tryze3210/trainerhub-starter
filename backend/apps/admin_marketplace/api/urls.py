from django.urls import path

from apps.admin_marketplace.api.views import AdminMarketplaceHealthView

urlpatterns = [
    path("marketplace-health/", AdminMarketplaceHealthView.as_view(), name="admin-marketplace-health"),
]
