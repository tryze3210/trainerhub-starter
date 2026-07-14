from django.urls import path

from apps.platform_settings.api.views import PaymentProviderSettingsView, PublicCheckoutPaymentSettingsView

urlpatterns = [
    path('payment-providers/', PaymentProviderSettingsView.as_view(), name='platform-payment-providers'),
    path('checkout-payment-providers/', PublicCheckoutPaymentSettingsView.as_view(), name='public-checkout-payment-providers'),
]
