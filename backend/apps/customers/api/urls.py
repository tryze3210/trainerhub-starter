from django.urls import path

from apps.customers.api.views import CustomerMarketplaceHubViewSet, TrainerCRMViewSet

urlpatterns = [
    path("hub/", CustomerMarketplaceHubViewSet.as_view({"get": "list"}), name="customer-marketplace-hub"),
    path("trainer-crm/", TrainerCRMViewSet.as_view({"get": "list"}), name="trainer-crm-list"),
    path("trainer-crm/<uuid:pk>/", TrainerCRMViewSet.as_view({"get": "retrieve"}), name="trainer-crm-detail"),
    path("trainer-crm/notes/", TrainerCRMViewSet.as_view({"post": "create_note"}), name="trainer-crm-note-create"),
    path("trainer-crm/segments/", TrainerCRMViewSet.as_view({"post": "create_segment"}), name="trainer-crm-segment-create"),
    path("trainer-crm/segments/assign/", TrainerCRMViewSet.as_view({"post": "assign_segment"}), name="trainer-crm-segment-assign"),
]
