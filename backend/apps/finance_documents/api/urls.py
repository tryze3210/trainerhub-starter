from django.urls import path
from apps.finance_documents.api import views

urlpatterns = [
    path("me/profile/", views.MyFinanceProfileView.as_view(), name="finance-documents-my-profile"),
    path("me/documents/", views.MyFinanceDocumentsView.as_view(), name="finance-documents-my-list"),
    path("me/statements/build/", views.BuildMyStatementView.as_view(), name="finance-documents-my-statement-build"),
    path("admin/documents/", views.AdminFinanceDocumentsView.as_view(), name="finance-documents-admin-list"),
    path("admin/documents/build/", views.AdminBuildFinanceDocumentView.as_view(), name="finance-documents-admin-build"),
    path("admin/documents/accountant-export/", views.AdminAccountantExportView.as_view(), name="finance-documents-admin-accountant-export"),
    path("admin/documents/<uuid:document_id>/finalize/", views.AdminFinalizeDocumentView.as_view(), name="finance-documents-admin-finalize"),
]
