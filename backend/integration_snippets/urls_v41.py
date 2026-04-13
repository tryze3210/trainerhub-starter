from django.urls import include, path

urlpatterns += [
    path("api/v1/booking/", include("apps.booking.api.urls")),
]
