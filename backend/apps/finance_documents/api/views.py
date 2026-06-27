from datetime import date
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access_control.permissions import IsFinanceOps
from apps.finance_documents.api.serializers import (
    AccountantExportQuerySerializer,
    BuildFinanceDocumentSerializer,
    FinanceDocumentSerializer,
    TrainerFinanceProfileSerializer,
)
from apps.finance_documents.models import FinanceDocument, TrainerFinanceProfile
from apps.finance_documents.services.commercial_documents import FinanceCommercialDocumentService
from apps.finance_documents.services.rendering import FinanceDocumentRenderer
from apps.finance_documents.services.statements import TrainerStatementService
from apps.orders.models import Order
from apps.payments.models import Payment


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
    permission_classes = [permissions.IsAuthenticated, IsFinanceOps]

    def get_queryset(self):
        queryset = FinanceDocument.objects.select_related("trainer").all()
        document_type = self.request.query_params.get("document_type")
        status_value = self.request.query_params.get("status")
        period_start = self.request.query_params.get("period_start")
        period_end = self.request.query_params.get("period_end")
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        if status_value:
            queryset = queryset.filter(status=status_value)
        if period_start:
            queryset = queryset.filter(period_end__gte=period_start)
        if period_end:
            queryset = queryset.filter(period_start__lte=period_end)
        return queryset


class AdminFinalizeDocumentView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsFinanceOps]

    def post(self, request, document_id):
        document = get_object_or_404(FinanceDocument, id=document_id)
        if not document.rendered_html:
            document.rendered_html = FinanceDocumentRenderer().render(document)
        document.status = FinanceDocument.STATUS_FINALIZED
        document.finalized_at = timezone.now()
        document.save(update_fields=["rendered_html", "status", "finalized_at", "updated_at"])
        return Response(FinanceDocumentSerializer(document).data)


class AdminBuildFinanceDocumentView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsFinanceOps]

    def post(self, request):
        serializer = BuildFinanceDocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        document_type = data["document_type"]
        if document_type in {FinanceDocument.DOC_INVOICE, FinanceDocument.DOC_RECEIPT}:
            order = get_object_or_404(Order.objects.select_related("user"), id=data.get("order_id"))
            payment = None
            if data.get("payment_id"):
                payment = get_object_or_404(Payment.objects.select_related("order", "order__user"), id=data["payment_id"])
            result = FinanceCommercialDocumentService.build_for_order(
                document_type=document_type,
                order=order,
                payment=payment,
                actor=request.user,
                request=request,
            )
        else:
            payment = get_object_or_404(Payment.objects.select_related("order", "order__user"), id=data.get("payment_id"))
            result = FinanceCommercialDocumentService.build_refund_document(
                document_type=document_type,
                payment=payment,
                refund_id=data.get("refund_id") or str(payment.id),
                amount=data.get("amount"),
                reason=data.get("reason", ""),
                actor=request.user,
                request=request,
            )
        return Response(
            {"created": result.created, "document": FinanceDocumentSerializer(result.document).data},
            status=status.HTTP_201_CREATED if result.created else status.HTTP_200_OK,
        )


class AdminAccountantExportView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsFinanceOps]

    def get(self, request):
        serializer = AccountantExportQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        queryset = FinanceDocument.objects.select_related("trainer").all()
        data = serializer.validated_data
        if data.get("document_type"):
            queryset = queryset.filter(document_type=data["document_type"])
        if data.get("status"):
            queryset = queryset.filter(status=data["status"])
        if data.get("period_start"):
            queryset = queryset.filter(period_end__gte=data["period_start"])
        if data.get("period_end"):
            queryset = queryset.filter(period_start__lte=data["period_end"])
        csv_body = FinanceCommercialDocumentService.export_for_accountant(queryset=queryset)
        response = HttpResponse(csv_body, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="finance_documents_accountant_export.csv"'
        return response
