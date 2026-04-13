from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from django.db import transaction
from django.utils import timezone

from apps.referrals.models import (
    ReferralAttribution,
    ReferralCode,
    ReferralInvite,
    ReferralLedger,
    ReferralProgram,
    ReferralReward,
)


@dataclass(frozen=True)
class LandingAttributionPayload:
    code: str
    landing_path: str = ""
    utm_source: str = ""
    utm_medium: str = ""
    utm_campaign: str = ""
    click_session_key: str = ""


class ReferralEngine:
    @staticmethod
    def track_landing(payload: LandingAttributionPayload) -> ReferralInvite:
        code = ReferralCode.objects.select_related("program").get(code=payload.code, is_active=True)
        invite = ReferralInvite.objects.create(
            code=code,
            landing_path=payload.landing_path,
            utm_source=payload.utm_source,
            utm_medium=payload.utm_medium,
            utm_campaign=payload.utm_campaign,
            click_session_key=payload.click_session_key,
        )
        return invite

    @staticmethod
    @transaction.atomic
    def bind_signup(invite: ReferralInvite, referred_user) -> ReferralAttribution:
        attribution, _ = ReferralAttribution.objects.get_or_create(
            invite=invite,
            defaults={
                "referred_user": referred_user,
                "attribution_model": "last_click",
                "is_locked": True,
            },
        )
        return attribution


class ReferralRewardService:
    @staticmethod
    @transaction.atomic
    def reward_for_paid_order(attribution: ReferralAttribution, trigger_reference: str) -> ReferralReward:
        program: ReferralProgram = attribution.invite.code.program
        reward = ReferralReward.objects.create(
            attribution=attribution,
            trigger_type="order_paid",
            trigger_reference=trigger_reference,
            amount=program.reward_amount or Decimal("0.00"),
            status=ReferralReward.STATUS_APPROVED,
        )
        owner = attribution.invite.code.owner
        last_balance = (
            ReferralLedger.objects.filter(owner=owner)
            .order_by("-created_at")
            .values_list("balance_after", flat=True)
            .first()
            or Decimal("0.00")
        )
        ReferralLedger.objects.create(
            owner=owner,
            reward=reward,
            entry_type=ReferralLedger.ENTRY_REWARD,
            amount=reward.amount,
            balance_after=last_balance + reward.amount,
        )
        invite = attribution.invite
        invite.status = ReferralInvite.STATUS_CONVERTED
        invite.converted_at = timezone.now()
        invite.save(update_fields=["status", "converted_at"])
        return reward
