from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.entitlements.api.views import EntitlementViewSet
from apps.orders.api.views import OrderViewSet
from apps.payments.api.views import PaymentViewSet, PaymentWebhookViewSet
from apps.subscriptions.api.views import SubscriptionViewSet

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='orders')
router.register(r'payments', PaymentViewSet, basename='payments')
router.register(r'payments-webhooks', PaymentWebhookViewSet, basename='payments-webhooks')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscriptions')
router.register(r'entitlements', EntitlementViewSet, basename='entitlements')

urlpatterns = [
    *router.urls,
    path('events/', include('apps.events.api.urls')),
    path('workflows/', include('apps.workflows.api.urls')),
    path('ops/', include('apps.ops.api.urls')),
]
