from django.urls import path
from apps.legal_compliance.api.views import (
    AcceptLegalDocumentView,
    AdminKYCQueueView,
    AdminKYCReviewView,
    AdminLegalDocumentsView,
    AdminPayoutEligibilityView,
    MeContractsView,
    MeConsentLogsView,
    MeLegalComplianceStatusView,
    MeLegalDocumentsView,
    MePayoutEligibilityView,
    MeTrainerKYCView,
)

urlpatterns = [
    path('me/kyc/', MeTrainerKYCView.as_view(), name='legal-me-kyc'),
    path('me/documents/', MeLegalDocumentsView.as_view(), name='legal-me-documents'),
    path('me/documents/<uuid:document_id>/accept/', AcceptLegalDocumentView.as_view(), name='legal-accept'),
    path('me/compliance-status/', MeLegalComplianceStatusView.as_view(), name='legal-me-compliance-status'),
    path('me/consent-logs/', MeConsentLogsView.as_view(), name='legal-me-consent-logs'),
    path('me/contracts/', MeContractsView.as_view(), name='legal-me-contracts'),
    path('me/payout-eligibility/', MePayoutEligibilityView.as_view(), name='legal-me-payout-eligibility'),
    path('admin/kyc/queue/', AdminKYCQueueView.as_view(), name='legal-admin-kyc-queue'),
    path('admin/kyc/<uuid:profile_id>/review/', AdminKYCReviewView.as_view(), name='legal-admin-kyc-review'),
    path('admin/documents/', AdminLegalDocumentsView.as_view(), name='legal-admin-documents'),
    path('admin/payout-eligibility/', AdminPayoutEligibilityView.as_view(), name='legal-admin-payout-eligibility'),
]
