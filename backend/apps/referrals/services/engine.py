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
    TRIGGER_ORDER_PAID = "order_paid"

    @staticmethod
    def _as_money(value: Decimal | str | int | float | None) -> Decimal:
        return Decimal(str(value if value is not None else Decimal("0.00"))).quantize(Decimal("0.01"))

    @classmethod
    def _calculate_reward_amount(
        cls,
        *,
        program: ReferralProgram,
        order_amount: Decimal | str | int | float | None = None,
    ) -> Decimal:
        reward_amount = cls._as_money(program.reward_amount)
        if program.reward_kind == "percent":
            if order_amount is None:
                return Decimal("0.00")
            return (cls._as_money(order_amount) * reward_amount / Decimal("100.00")).quantize(Decimal("0.01"))
        return reward_amount

    @staticmethod
    def _last_balance_for_update(owner) -> Decimal:
        return (
            ReferralLedger.objects.select_for_update()
            .filter(owner=owner)
            .order_by("-created_at")
            .values_list("balance_after", flat=True)
            .first()
            or Decimal("0.00")
        )

    @classmethod
    @transaction.atomic
    def reward_for_paid_order(
        cls,
        attribution: ReferralAttribution,
        trigger_reference: str,
        order_amount: Decimal | str | int | float | None = None,
    ) -> ReferralReward:
        """Create exactly one approved referral reward for one paid-order trigger.

        Payment webhooks are at-least-once delivered. This service is therefore
        intentionally idempotent by business key:
        attribution + trigger_type + trigger_reference.
        """
        trigger_reference = str(trigger_reference or "").strip()
        if not trigger_reference:
            raise ValueError("trigger_reference is required for referral reward idempotency.")

        attribution = (
            ReferralAttribution.objects.select_for_update()
            .select_related("invite__code__program", "invite__code__owner")
            .get(pk=attribution.pk)
        )

        existing = (
            ReferralReward.objects.select_related("attribution__invite__code__owner")
            .filter(
                attribution=attribution,
                trigger_type=cls.TRIGGER_ORDER_PAID,
                trigger_reference=trigger_reference,
            )
            .first()
        )
        if existing:
            return existing

        program: ReferralProgram = attribution.invite.code.program
        reward = ReferralReward.objects.create(
            attribution=attribution,
            trigger_type=cls.TRIGGER_ORDER_PAID,
            trigger_reference=trigger_reference,
            amount=cls._calculate_reward_amount(program=program, order_amount=order_amount),
            status=ReferralReward.STATUS_APPROVED,
        )

        owner = attribution.invite.code.owner
        last_balance = cls._last_balance_for_update(owner)
        ReferralLedger.objects.create(
            owner=owner,
            reward=reward,
            entry_type=ReferralLedger.ENTRY_REWARD,
            amount=reward.amount,
            balance_after=last_balance + reward.amount,
        )

        invite = attribution.invite
        if invite.status != ReferralInvite.STATUS_CONVERTED:
            invite.status = ReferralInvite.STATUS_CONVERTED
            invite.converted_at = timezone.now()
            invite.save(update_fields=["status", "converted_at"])

        return reward
