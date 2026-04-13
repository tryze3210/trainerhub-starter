from django.urls import path
from .views import PurchaseCheckoutApi, PurchaseListApi

urlpatterns = [
    path("checkout/", PurchaseCheckoutApi.as_view(), name="purchase-checkout"),
    path("me/", PurchaseListApi.as_view(), name="purchase-list"),
]
