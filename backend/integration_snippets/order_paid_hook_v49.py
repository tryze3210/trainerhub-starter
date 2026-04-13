"""
Call this from your paid order application service.
"""

from apps.referrals.models import ReferralAttribution
from apps.referrals.services import ReferralRewardService


def reward_referrer_for_paid_order(*, referred_user, order_reference: str):
    attribution = (
        ReferralAttribution.objects.select_related("invite__code__program")
        .filter(referred_user=referred_user, is_locked=True)
        .order_by("-created_at")
        .first()
    )
    if not attribution:
        return None
    return ReferralRewardService.reward_for_paid_order(
        attribution=attribution,
        trigger_reference=order_reference,
    )
