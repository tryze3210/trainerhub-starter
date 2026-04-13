from django.urls import path
from .views import ProductListCreateApi, ProductDetailApi

urlpatterns = [
    path("", ProductListCreateApi.as_view(), name="product-list-create"),
    path("<slug:slug>/", ProductDetailApi.as_view(), name="product-detail"),
]
