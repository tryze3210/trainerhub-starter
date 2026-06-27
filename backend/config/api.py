from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.entitlements.api.views import EntitlementViewSet
from apps.orders.api.views import OrderViewSet
from apps.payments.api.views import AdminPaymentViewSet, PaymentViewSet, PaymentWebhookViewSet
from apps.subscriptions.api.views import SubscriptionViewSet

router = DefaultRouter()
router.register(r"orders", OrderViewSet, basename="orders")
router.register(r"payments", PaymentViewSet, basename="payments")
router.register(r"payments-admin", AdminPaymentViewSet, basename="payments-admin")
router.register(r"payments-webhooks", PaymentWebhookViewSet, basename="payments-webhooks")
router.register(r"subscriptions", SubscriptionViewSet, basename="subscriptions")
router.register(r"entitlements", EntitlementViewSet, basename="entitlements")

urlpatterns = [
    *router.urls,
    path("events/", include("apps.events.api.urls")),
    path("workflows/", include("apps.workflows.api.urls")),
    path("ops/", include("apps.ops.api.urls")),
    path("progress/", include("apps.progress.api.urls")),
    path("assignments/", include("apps.assignments.api.urls")),
    path("messaging/", include("apps.messaging.api.urls")),
    path("products/", include("apps.products.api.trainer_urls")),
    path("disputes/", include("apps.disputes.api.urls")),
    path("finance-documents/", include("apps.finance_documents.api.urls")),
    path("legal/", include("apps.legal_compliance.api.urls")),
    path("observability/", include("apps.observability.api.urls")),
]
