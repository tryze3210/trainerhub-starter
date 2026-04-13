from django.apps import apps
from rest_framework import permissions, response, status, views

from apps.finance_documents.services.download_urls import FinanceDocumentDownloadURLService
from apps.finance_documents.services.storage import DummyArtifactStorage
from apps.finance_documents.tasks import generate_finance_document_artifact, deliver_finance_document_email


class MyFinanceDocumentDownloadURLView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, document_id):
        FinanceDocument = apps.get_model("finance_documents", "FinanceDocument")
        document = FinanceDocument.objects.get(id=document_id, trainer=request.user)
        url = FinanceDocumentDownloadURLService(DummyArtifactStorage()).build_url(document=document)
        return response.Response({"document_id": str(document.id), "download_url": url})


class AdminFinanceDocumentDownloadURLView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, document_id):
        FinanceDocument = apps.get_model("finance_documents", "FinanceDocument")
        document = FinanceDocument.objects.get(id=document_id)
        url = FinanceDocumentDownloadURLService(DummyArtifactStorage()).build_url(document=document)
        return response.Response({"document_id": str(document.id), "download_url": url})


class AdminGenerateFinanceDocumentArtifactView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, document_id):
        generate_finance_document_artifact.delay(str(document_id))
        return response.Response({"status": "queued"}, status=status.HTTP_202_ACCEPTED)


class AdminDeliverFinanceDocumentEmailView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, document_id):
        deliver_finance_document_email.delay(str(document_id))
        return response.Response({"status": "queued"}, status=status.HTTP_202_ACCEPTED)
