from django.urls import path
from apps.finance_documents.api import views

urlpatterns = [
    path("me/profile/", views.MyFinanceProfileView.as_view()),
    path("me/documents/", views.MyFinanceDocumentsView.as_view()),
    path("me/statements/build/", views.BuildMyStatementView.as_view()),
    path("admin/documents/", views.AdminFinanceDocumentsView.as_view()),
    path("admin/documents/<uuid:document_id>/finalize/", views.AdminFinalizeDocumentView.as_view()),
]
