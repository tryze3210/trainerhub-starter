from apps.legal_compliance.services.eligibility import PayoutEligibilityService


def assert_trainer_payout_eligible(trainer):
    snapshot = PayoutEligibilityService.refresh_snapshot(trainer)
    if not snapshot.is_eligible:
        raise ValueError(f'Payout blocked: {snapshot.block_reason}')
    return snapshot
