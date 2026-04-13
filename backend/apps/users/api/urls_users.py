from django.urls import path
from .views_users import MeApi

urlpatterns = [
    path("me/", MeApi.as_view()),
]
