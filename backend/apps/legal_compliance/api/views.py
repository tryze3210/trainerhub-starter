from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from apps.legal_compliance.models import (
    LegalDocumentTemplate,
    PayoutEligibilitySnapshot,
    TrainerContractArtifact,
    TrainerKYCProfile,
)
from apps.legal_compliance.api.serializers import (
    ConsentLogSerializer,
    LegalAcceptanceSnapshotSerializer,
    LegalComplianceStatusSerializer,
    LegalDocumentTemplateSerializer,
    PayoutEligibilitySnapshotSerializer,
    TrainerContractArtifactSerializer,
    TrainerKYCProfileSerializer,
)
from apps.legal_compliance.services.acceptance import LegalAcceptanceService
from apps.legal_compliance.services.eligibility import PayoutEligibilityService


class MeTrainerKYCView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TrainerKYCProfileSerializer

    def get_object(self):
        profile, _ = TrainerKYCProfile.objects.get_or_create(trainer=self.request.user)
        return profile


class MeLegalDocumentsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LegalDocumentTemplateSerializer

    def get_queryset(self):
        document_ids = [document.id for document in LegalAcceptanceService.active_current_documents()]
        return LegalDocumentTemplate.objects.filter(id__in=document_ids).order_by('doc_type', '-published_at')


class AcceptLegalDocumentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, document_id):
        document = LegalDocumentTemplate.objects.get(id=document_id, is_active=True)
        actor_type = 'trainer' if request.query_params.get('actor') == 'trainer' else 'user'
        try:
            acceptance = LegalAcceptanceService.accept_document(
                user=request.user,
                actor_type=actor_type,
                document=document,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        compliance = LegalAcceptanceService.compliance_status(user=request.user, actor_type=actor_type)
        return Response(
            {
                'status': 'accepted',
                'acceptance': LegalAcceptanceSnapshotSerializer(acceptance).data,
                'compliance': LegalComplianceStatusSerializer(compliance).data,
            },
            status=status.HTTP_201_CREATED,
        )


class MeLegalComplianceStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        actor_type = 'trainer' if request.query_params.get('actor') == 'trainer' else 'user'
        payload = LegalAcceptanceService.compliance_status(user=request.user, actor_type=actor_type)
        return Response(LegalComplianceStatusSerializer(payload).data)


class MeConsentLogsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ConsentLogSerializer

    def get_queryset(self):
        return self.request.user.consent_logs.order_by('-recorded_at')


class MeContractsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TrainerContractArtifactSerializer

    def get_queryset(self):
        return TrainerContractArtifact.objects.filter(trainer=self.request.user).order_by('-created_at')


class MePayoutEligibilityView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        snapshot = PayoutEligibilityService.refresh_snapshot(request.user)
        return Response(PayoutEligibilitySnapshotSerializer(snapshot).data)


class AdminKYCQueueView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = TrainerKYCProfileSerializer

    def get_queryset(self):
        return TrainerKYCProfile.objects.all().order_by('status', '-updated_at')


class AdminKYCReviewView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, profile_id):
        profile = TrainerKYCProfile.objects.get(id=profile_id)
        decision = request.data.get('decision')
        if decision == 'approve':
            missing = [
                field
                for field in ('full_name', 'country', 'tax_id', 'legal_address', 'payout_legal_entity_name')
                if not getattr(profile, field)
            ]
            if missing:
                return Response(
                    {'detail': 'KYC profile is incomplete.', 'missing_fields': missing},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            profile.status = TrainerKYCProfile.STATUS_APPROVED
            profile.rejection_reason = ''
        elif decision == 'reject':
            rejection_reason = request.data.get('rejection_reason', '').strip()
            if not rejection_reason:
                return Response(
                    {'detail': 'rejection_reason is required when rejecting KYC.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            profile.status = TrainerKYCProfile.STATUS_REJECTED
            profile.rejection_reason = rejection_reason
        else:
            return Response(
                {'detail': 'decision must be approve or reject.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        profile.reviewed_by = request.user
        profile.reviewed_at = timezone.now()
        profile.save(update_fields=['status', 'rejection_reason', 'reviewed_by', 'reviewed_at', 'updated_at'])
        PayoutEligibilityService.refresh_snapshot(profile.trainer)
        return Response({'status': profile.status})


class AdminLegalDocumentsView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = LegalDocumentTemplateSerializer
    queryset = LegalDocumentTemplate.objects.all().order_by('doc_type', '-published_at', '-created_at')


class AdminPayoutEligibilityView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = PayoutEligibilitySnapshotSerializer
    queryset = PayoutEligibilitySnapshot.objects.all().order_by('is_eligible', 'calculated_at')
