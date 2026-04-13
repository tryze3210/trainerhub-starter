from rest_framework import serializers

from apps.accounting_integration.models import (
    AccountMappingRule,
    ChartOfAccount,
    ExternalAccountingSystem,
    GLExportRun,
    JournalBatch,
)


class ExternalAccountingSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalAccountingSystem
        fields = [
            "id",
            "code",
            "name",
            "is_active",
            "adapter_key",
            "base_currency",
            "settings_json",
            "created_at",
            "updated_at",
        ]


class ChartOfAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChartOfAccount
        fields = [
            "id",
            "system",
            "code",
            "name",
            "account_type",
            "currency",
            "is_active",
        ]


class AccountMappingRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountMappingRule
        fields = [
            "id",
            "system",
            "target_type",
            "source_code",
            "account",
            "effective_from",
            "effective_to",
            "priority",
            "metadata",
            "is_active",
        ]


class JournalBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalBatch
        fields = [
            "id",
            "system",
            "period",
            "snapshot",
            "status",
            "batch_number",
            "description",
            "currency",
            "total_debit",
            "total_credit",
            "finalized_at",
            "exported_at",
            "metadata",
            "created_at",
        ]


class GLExportRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = GLExportRun
        fields = [
            "id",
            "system",
            "period",
            "journal_batch",
            "export_format",
            "status",
            "run_number",
            "idempotency_key",
            "payload",
            "file_path",
            "checksum",
            "exported_at",
            "delivered_at",
            "failure_reason",
            "supersedes",
            "created_at",
        ]
