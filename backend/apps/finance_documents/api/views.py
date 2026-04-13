from datetime import date
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.finance_documents.api.serializers import FinanceDocumentSerializer, TrainerFinanceProfileSerializer
from apps.finance_documents.models import FinanceDocument, TrainerFinanceProfile
from apps.finance_documents.services.rendering import FinanceDocumentRenderer
from apps.finance_documents.services.statements import TrainerStatementService


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


class MyFinanceProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = TrainerFinanceProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj, _ = TrainerFinanceProfile.objects.get_or_create(trainer=self.request.user)
        return obj


class MyFinanceDocumentsView(generics.ListAPIView):
    serializer_class = FinanceDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FinanceDocument.objects.filter(trainer=self.request.user)


class BuildMyStatementView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        today = timezone.now().date()
        start = date(today.year, today.month, 1)
        service = TrainerStatementService()
        document = service.build_monthly_statement(trainer=request.user, period_start=start, period_end=today)
        document.rendered_html = FinanceDocumentRenderer().render(document)
        document.save(update_fields=["rendered_html", "updated_at"])
        return Response(FinanceDocumentSerializer(document).data, status=status.HTTP_201_CREATED)


class AdminFinanceDocumentsView(generics.ListAPIView):
    serializer_class = FinanceDocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = FinanceDocument.objects.all()


class AdminFinalizeDocumentView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def post(self, request, document_id):
        document = get_object_or_404(FinanceDocument, id=document_id)
        if not document.rendered_html:
            document.rendered_html = FinanceDocumentRenderer().render(document)
        document.status = FinanceDocument.STATUS_FINALIZED
        document.finalized_at = timezone.now()
        document.save(update_fields=["rendered_html", "status", "finalized_at", "updated_at"])
        return Response(FinanceDocumentSerializer(document).data)
