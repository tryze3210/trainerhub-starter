from django.urls import path
from .views import CategoryListApi

urlpatterns = [
    path("", CategoryListApi.as_view(), name="category-list"),
]
