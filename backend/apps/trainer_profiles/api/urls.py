from django.urls import path

from apps.trainer_profiles.api.views import PublicTrainerDetailView, PublicTrainerListView

urlpatterns = [
    path('', PublicTrainerListView.as_view(), name='public-trainer-list'),
    path('<slug:slug>/', PublicTrainerDetailView.as_view(), name='public-trainer-detail'),
]
