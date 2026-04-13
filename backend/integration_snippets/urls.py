from django.urls import include, path

urlpatterns += [
    path("api/v1/finance-documents/", include("apps.finance_documents.api.urls")),
]
