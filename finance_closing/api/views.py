from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from finance_closing.api.serializers import (
    AccountingDocumentSerializer,
    ClosingPeriodSerializer,
    FinanceCloseAuditLogSerializer,
    FinanceSnapshotSerializer,
    TrainerMonthStatementSerializer,
)
from finance_closing.models import AccountingDocument, ClosingPeriod, FinanceCloseAuditLog, FinanceSnapshot, TrainerMonthStatement
from finance_closing.services.closing_service import FinanceClosingService
from finance_closing.services.document_service import CreditNoteService


class ClosingPeriodAdminViewSet(viewsets.ModelViewSet):
    queryset = ClosingPeriod.objects.all().order_by('-starts_at')
    serializer_class = ClosingPeriodSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        period = self.get_object()
        period = FinanceClosingService.close_period(period=period, actor=request.user)
        return Response(self.get_serializer(period).data)

    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        period = self.get_object()
        period = FinanceClosingService.reopen_period(
            period=period,
            actor=request.user,
            reason=request.data.get('reason', ''),
        )
        return Response(self.get_serializer(period).data)


class FinanceSnapshotAdminViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FinanceSnapshot.objects.select_related('period').all().order_by('-created_at')
    serializer_class = FinanceSnapshotSerializer
    permission_classes = [IsAdminUser]


class TrainerMonthStatementAdminViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TrainerMonthStatement.objects.select_related('trainer', 'period', 'snapshot', 'accounting_document').all()
    serializer_class = TrainerMonthStatementSerializer
    permission_classes = [IsAdminUser]


class AccountingDocumentAdminViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AccountingDocument.objects.select_related('period', 'trainer').prefetch_related('lines').all()
    serializer_class = AccountingDocumentSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=['post'])
    def issue_credit_note(self, request, pk=None):
        document = self.get_object()
        credit_note = CreditNoteService.issue_credit_note(
            replaced_document=document,
            reason=request.data.get('reason', ''),
            line_items=request.data.get('line_items', []),
        )
        return Response(self.get_serializer(credit_note).data, status=status.HTTP_201_CREATED)


class FinanceCloseAuditLogAdminViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FinanceCloseAuditLog.objects.select_related('period', 'actor').all().order_by('-created_at')
    serializer_class = FinanceCloseAuditLogSerializer
    permission_classes = [IsAdminUser]
