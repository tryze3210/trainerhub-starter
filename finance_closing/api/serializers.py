from rest_framework import serializers

from finance_closing.models import (
    AccountingDocument,
    AccountingDocumentLine,
    ClosingPeriod,
    FinanceCloseAuditLog,
    FinanceSnapshot,
    TrainerMonthStatement,
)


class FinanceSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinanceSnapshot
        fields = ['id', 'period', 'status', 'version', 'ledger_cutoff_at', 'payload', 'generated_at']


class ClosingPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClosingPeriod
        fields = [
            'id', 'code', 'starts_at', 'ends_at', 'currency', 'legal_entity_code',
            'status', 'closed_at', 'notes',
        ]


class AccountingDocumentLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountingDocumentLine
        fields = ['id', 'sort_order', 'code', 'description', 'quantity', 'unit_amount', 'line_amount', 'tax_rate', 'metadata']


class AccountingDocumentSerializer(serializers.ModelSerializer):
    lines = AccountingDocumentLineSerializer(many=True, read_only=True)

    class Meta:
        model = AccountingDocument
        fields = [
            'id', 'document_type', 'status', 'number', 'period', 'trainer', 'currency',
            'subtotal_amount', 'tax_amount', 'total_amount', 'issued_at', 'voided_at',
            'replaces_document', 'payload', 'lines',
        ]


class TrainerMonthStatementSerializer(serializers.ModelSerializer):
    accounting_document = AccountingDocumentSerializer(read_only=True)

    class Meta:
        model = TrainerMonthStatement
        fields = [
            'id', 'trainer', 'period', 'snapshot', 'currency', 'gross_sales_amount',
            'refunds_amount', 'commission_amount', 'payout_fees_amount', 'reserve_amount',
            'net_payable_amount', 'line_items', 'issued_at', 'accounting_document',
        ]


class FinanceCloseAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinanceCloseAuditLog
        fields = ['id', 'period', 'actor', 'action', 'details', 'created_at']
