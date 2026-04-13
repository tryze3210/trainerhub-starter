from dataclasses import dataclass
from django.contrib.auth import get_user_model
from apps.legal_compliance.models import (
    PayoutEligibilitySnapshot,
    TrainerContractArtifact,
    TrainerKYCProfile,
)

User = get_user_model()


@dataclass
class EligibilityResult:
    is_eligible: bool
    block_reason: str
    has_active_agreement: bool
    has_verified_payout_profile: bool
    kyc_status: str


class PayoutEligibilityService:
    @classmethod
    def evaluate_for_trainer(cls, trainer: User) -> EligibilityResult:
        kyc = getattr(trainer, 'trainer_kyc_profile', None)
        active_contract = TrainerContractArtifact.objects.filter(
            trainer=trainer,
            status__in=[TrainerContractArtifact.STATUS_GENERATED, TrainerContractArtifact.STATUS_SIGNED],
        ).exists()
        has_profile = bool(kyc and kyc.payout_legal_entity_name and kyc.tax_id)
        kyc_status = kyc.status if kyc else ''

        reasons = []
        if not kyc:
            reasons.append('kyc_profile_missing')
        elif kyc.status != TrainerKYCProfile.STATUS_APPROVED:
            reasons.append('kyc_not_approved')
        if not has_profile:
            reasons.append('payout_profile_incomplete')
        if not active_contract:
            reasons.append('active_trainer_agreement_missing')

        return EligibilityResult(
            is_eligible=not reasons,
            block_reason=', '.join(reasons),
            has_active_agreement=active_contract,
            has_verified_payout_profile=has_profile,
            kyc_status=kyc_status,
        )

    @classmethod
    def refresh_snapshot(cls, trainer: User) -> PayoutEligibilitySnapshot:
        result = cls.evaluate_for_trainer(trainer)
        snapshot, _ = PayoutEligibilitySnapshot.objects.update_or_create(
            trainer=trainer,
            defaults={
                'kyc_status': result.kyc_status,
                'has_active_agreement': result.has_active_agreement,
                'has_verified_payout_profile': result.has_verified_payout_profile,
                'is_eligible': result.is_eligible,
                'block_reason': result.block_reason,
            },
        )
        return snapshot
