from django.urls import path

from .views_v36 import (
    AdminDeliverFinanceDocumentEmailView,
    AdminFinanceDocumentDownloadURLView,
    AdminGenerateFinanceDocumentArtifactView,
    MyFinanceDocumentDownloadURLView,
)

urlpatterns = [
    path("me/documents/<uuid:document_id>/download-url/", MyFinanceDocumentDownloadURLView.as_view()),
    path("admin/documents/<uuid:document_id>/download-url/", AdminFinanceDocumentDownloadURLView.as_view()),
    path("admin/documents/<uuid:document_id>/generate-artifact/", AdminGenerateFinanceDocumentArtifactView.as_view()),
    path("admin/documents/<uuid:document_id>/deliver-email/", AdminDeliverFinanceDocumentEmailView.as_view()),
]
