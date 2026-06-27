from rest_framework import serializers
from apps.legal_compliance.models import (
    ConsentLog,
    LegalAcceptanceSnapshot,
    LegalDocumentTemplate,
    PayoutEligibilitySnapshot,
    TrainerContractArtifact,
    TrainerKYCProfile,
)


class TrainerKYCProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerKYCProfile
        fields = '__all__'
        read_only_fields = ('trainer', 'reviewed_by', 'reviewed_at', 'created_at', 'updated_at')


class LegalDocumentTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalDocumentTemplate
        fields = '__all__'


class LegalAcceptanceSnapshotSerializer(serializers.ModelSerializer):
    document_title = serializers.CharField(source='document.title', read_only=True)

    class Meta:
        model = LegalAcceptanceSnapshot
        fields = '__all__'


class ConsentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsentLog
        fields = '__all__'


class LegalComplianceStatusSerializer(serializers.Serializer):
    actor_type = serializers.CharField()
    is_compliant = serializers.BooleanField()
    missing = serializers.ListField(child=serializers.CharField())
    documents = serializers.DictField()


class TrainerContractArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerContractArtifact
        fields = '__all__'


class PayoutEligibilitySnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayoutEligibilitySnapshot
        fields = '__all__'
