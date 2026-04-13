"""
Call this from your registration application service after user is created.
"""

from apps.referrals.models import ReferralInvite
from apps.referrals.services import ReferralEngine


def attach_referral_after_signup(*, user, invite_id: str | None):
    if not invite_id:
        return None
    invite = ReferralInvite.objects.get(id=invite_id)
    return ReferralEngine.bind_signup(invite=invite, referred_user=user)
