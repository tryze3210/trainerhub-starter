from django.urls import path
from .views import (
    TrainerApplicationApi,
    TrainerApplicationSubmitApi,
    TrainerCatalogApi,
    TrainerDetailApi,
    TrainerMeProfileApi,
)

urlpatterns = [
    path('', TrainerCatalogApi.as_view(), name='trainer-catalog'),
    path('me/application/', TrainerApplicationApi.as_view(), name='trainer-me-application'),
    path('me/application/submit/', TrainerApplicationSubmitApi.as_view(), name='trainer-me-application-submit'),
    path('me/profile/', TrainerMeProfileApi.as_view(), name='trainer-me-profile'),
    path('<slug:slug>/', TrainerDetailApi.as_view(), name='trainer-detail'),
]
