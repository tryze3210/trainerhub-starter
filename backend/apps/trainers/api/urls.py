from django.urls import path
from .views import TrainerCatalogApi, TrainerDetailApi, TrainerMeProfileApi

urlpatterns = [
    path("", TrainerCatalogApi.as_view(), name="trainer-catalog"),
    path("me/profile/", TrainerMeProfileApi.as_view(), name="trainer-me-profile"),
    path("<slug:slug>/", TrainerDetailApi.as_view(), name="trainer-detail"),
]
