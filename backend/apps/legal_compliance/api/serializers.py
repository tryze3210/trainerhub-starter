from rest_framework import serializers
from apps.legal_compliance.models import (
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


class TrainerContractArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerContractArtifact
        fields = '__all__'


class PayoutEligibilitySnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayoutEligibilitySnapshot
        fields = '__all__'
