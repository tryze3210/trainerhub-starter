from django.urls import path

from apps.customers.api.views import CustomerMarketplaceHubViewSet

urlpatterns = [
    path("hub/", CustomerMarketplaceHubViewSet.as_view({"get": "list"}), name="customer-marketplace-hub"),
]
