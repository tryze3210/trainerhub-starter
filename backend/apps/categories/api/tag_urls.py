from django.urls import path

from .views import TagListApi

urlpatterns = [
    path('', TagListApi.as_view(), name='tag-list'),
]
