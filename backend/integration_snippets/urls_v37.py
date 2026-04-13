from django.urls import include, path

urlpatterns += [
    path('api/v1/legal/', include('apps.legal_compliance.api.urls')),
]
