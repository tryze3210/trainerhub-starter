from django.urls import include, path

urlpatterns += [
    path("api/v1/moderation/", include("apps.moderation.api.urls")),
]
