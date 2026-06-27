from rest_framework import serializers
from apps.finance_documents.models import FinanceDocument, TrainerFinanceProfile


class TrainerFinanceProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerFinanceProfile
        fields = [
            "legal_name",
            "tax_number",
            "bank_name",
            "bank_account",
            "bank_bic",
            "payout_currency",
            "is_verified",
        ]
        read_only_fields = ["is_verified"]


class FinanceDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinanceDocument
        fields = [
            "id",
            "document_type",
            "status",
            "period_start",
            "period_end",
            "document_number",
            "currency",
            "gross_amount",
            "commission_amount",
            "net_amount",
            "artifact_path",
            "finalized_at",
            "created_at",
        ]


class BuildFinanceDocumentSerializer(serializers.Serializer):
    document_type = serializers.ChoiceField(
        choices=[
            FinanceDocument.DOC_INVOICE,
            FinanceDocument.DOC_RECEIPT,
            FinanceDocument.DOC_CREDIT_NOTE,
            FinanceDocument.DOC_REFUND_DOCUMENT,
        ]
    )
    order_id = serializers.UUIDField(required=False)
    payment_id = serializers.UUIDField(required=False)
    refund_id = serializers.CharField(required=False, allow_blank=True, max_length=128)
    amount = serializers.DecimalField(required=False, max_digits=12, decimal_places=2)
    reason = serializers.CharField(required=False, allow_blank=True)


class AccountantExportQuerySerializer(serializers.Serializer):
    document_type = serializers.ChoiceField(choices=FinanceDocument.DOC_CHOICES, required=False)
    status = serializers.ChoiceField(choices=FinanceDocument.STATUS_CHOICES, required=False)
    period_start = serializers.DateField(required=False)
    period_end = serializers.DateField(required=False)
