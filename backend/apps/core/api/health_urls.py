from django.urls import path
from .health_views import live, ready

urlpatterns = [
    path("live/", live),
    path("ready/", ready),
]
