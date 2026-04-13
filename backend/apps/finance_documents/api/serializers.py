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
