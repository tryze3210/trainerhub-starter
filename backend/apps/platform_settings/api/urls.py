from django.urls import path

from apps.platform_settings.api.views import PaymentProviderSettingsView

urlpatterns = [
    path('payment-providers/', PaymentProviderSettingsView.as_view(), name='platform-payment-providers'),
]
