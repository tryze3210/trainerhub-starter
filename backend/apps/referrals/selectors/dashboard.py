from django.db.models import Sum

from apps.referrals.models import ReferralCode, ReferralInvite, ReferralLedger, ReferralReward


def get_user_referral_dashboard(user):
    total_codes = ReferralCode.objects.filter(owner=user).count()
    total_invites = ReferralInvite.objects.filter(code__owner=user).count()
    conversions = ReferralInvite.objects.filter(
        code__owner=user,
        status=ReferralInvite.STATUS_CONVERTED,
    ).count()
    earned = (
        ReferralLedger.objects.filter(owner=user, entry_type=ReferralLedger.ENTRY_REWARD)
        .aggregate(total=Sum("amount"))
        .get("total")
        or 0
    )
    return {
        "total_codes": total_codes,
        "total_invites": total_invites,
        "conversions": conversions,
        "earned": earned,
    }
