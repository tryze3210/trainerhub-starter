from __future__ import annotations

from typing import Any
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from apps.referrals.models import ReferralAttribution, ReferralInvite, ReferralReward
from apps.referrals.services import ReferralEngine, ReferralRewardService


def _uuid_or_none(value: Any) -> UUID | None:
    if value in (None, ''):
        return None
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


class ReferralIntegrationService:
    """Integration bridge between auth, checkout, payments and the referrals bounded context.

    The referrals engine stays isolated: auth/order/payment services call this bridge instead
    of importing referral models directly. That gives us one stable seam for future event/outbox
    consumers and keeps growth attribution from leaking into core commercial code.
    """

    @staticmethod
    def bind_signup_from_request(
        *,
        referred_user,
        invite_id: str | UUID | None = None,
        referral_code: str = '',
        click_session_key: str = '',
    ) -> ReferralAttribution | None:
        """Attach the first valid pending referral invite to a registered user.

        Rules are intentionally strict:
        - one user can have only one referral attribution;
        - self-referral is rejected;
        - expired or already converted invites are ignored;
        - invite id has priority over code/session lookup.
        """
        if not referred_user or not getattr(referred_user, 'pk', None):
            return None

        existing = ReferralAttribution.objects.filter(referred_user=referred_user).first()
        if existing:
            return existing

        now = timezone.now()
        invite = None
        invite_uuid = _uuid_or_none(invite_id)
        qs = ReferralInvite.objects.select_related('code', 'code__owner', 'code__program')

        if invite_uuid:
            invite = qs.filter(id=invite_uuid).first()

        normalized_code = (referral_code or '').strip().upper()
        if invite is None and normalized_code:
            invite = (
                qs.filter(code__code=normalized_code, status=ReferralInvite.STATUS_PENDING)
                .order_by('-created_at')
                .first()
            )

        normalized_session_key = (click_session_key or '').strip()
        if invite is None and normalized_session_key:
            invite = (
                qs.filter(click_session_key=normalized_session_key, status=ReferralInvite.STATUS_PENDING)
                .order_by('-created_at')
                .first()
            )

        if invite is None:
            return None

        if invite.status != ReferralInvite.STATUS_PENDING:
            return None

        if invite.expires_at and invite.expires_at <= now:
            invite.status = ReferralInvite.STATUS_EXPIRED
            invite.save(update_fields=['status'])
            return None

        if invite.code.owner_id == referred_user.pk:
            return None

        with transaction.atomic():
            locked_invite = (
                ReferralInvite.objects.select_for_update()
                .select_related('code', 'code__owner', 'code__program')
                .get(pk=invite.pk)
            )
            if locked_invite.status != ReferralInvite.STATUS_PENDING:
                return None
            if locked_invite.code.owner_id == referred_user.pk:
                return None
            if locked_invite.expires_at and locked_invite.expires_at <= timezone.now():
                locked_invite.status = ReferralInvite.STATUS_EXPIRED
                locked_invite.save(update_fields=['status'])
                return None
            existing = ReferralAttribution.objects.select_for_update().filter(referred_user=referred_user).first()
            if existing:
                return existing
            return ReferralEngine.bind_signup(locked_invite, referred_user)

    @staticmethod
    def reward_for_paid_order_if_eligible(*, order, payment=None) -> ReferralReward | None:
        """Accrue a referral reward once for a paid order.

        Idempotency key is the order id. Repeated payment webhooks return the existing reward
        and do not create duplicate ledger entries.
        """
        user = getattr(order, 'user', None)
        if not user or not getattr(user, 'pk', None):
            return None

        attribution = (
            ReferralAttribution.objects.select_related('invite', 'invite__code', 'invite__code__program')
            .filter(referred_user=user)
            .order_by('created_at')
            .first()
        )
        if not attribution:
            return None

        trigger_reference = str(getattr(order, 'id'))
        existing_reward = ReferralReward.objects.filter(
            attribution=attribution,
            trigger_type='order_paid',
            trigger_reference=trigger_reference,
        ).first()
        if existing_reward:
            return existing_reward

        return ReferralRewardService.reward_for_paid_order(
            attribution=attribution,
            trigger_reference=trigger_reference,
        )
