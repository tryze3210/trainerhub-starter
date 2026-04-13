from rest_framework.routers import DefaultRouter
from apps.orders.api.views import OrderViewSet
from apps.payments.api.views import PaymentViewSet, PaymentWebhookViewSet
from apps.subscriptions.api.views import SubscriptionViewSet
from apps.entitlements.api.views import EntitlementViewSet

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='orders')
router.register(r'payments', PaymentViewSet, basename='payments')
router.register(r'payments-webhooks', PaymentWebhookViewSet, basename='payments-webhooks')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscriptions')
router.register(r'entitlements', EntitlementViewSet, basename='entitlements')

urlpatterns = router.urls
