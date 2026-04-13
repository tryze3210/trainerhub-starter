from django.urls import path
from .views_auth import RegisterApi, LoginApi, RefreshApi

urlpatterns = [
    path("register/", RegisterApi.as_view(), name="register"),
    path("login/", LoginApi.as_view(), name="login"),
    path("refresh/", RefreshApi.as_view(), name="refresh"),
]
