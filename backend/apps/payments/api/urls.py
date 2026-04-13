from django.urls import path
from .views import PaymentListApi, StubConfirmPaymentApi

urlpatterns = [
    path("me/", PaymentListApi.as_view(), name="payment-list"),
    path("<uuid:payment_id>/stub-confirm/", StubConfirmPaymentApi.as_view(), name="payment-stub-confirm"),
]
