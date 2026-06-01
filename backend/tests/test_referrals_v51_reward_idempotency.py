from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.referrals.models import ReferralCode, ReferralInvite, ReferralLedger, ReferralProgram, ReferralReward
from apps.referrals.services import ReferralEngine, ReferralRewardService


@pytest.mark.django_db
def test_paid_order_referral_reward_is_idempotent_by_trigger_reference():
    User = get_user_model()
    owner = User.objects.create_user(email="ref-owner@example.com", password="strong-pass-123")
    referred = User.objects.create_user(email="buyer-v51@example.com", password="strong-pass-123")

    program = ReferralProgram.objects.create(
        slug="ambassador-v51",
        name="Ambassador v51",
        reward_kind="fixed",
        reward_amount=Decimal("250.00"),
    )
    code = ReferralCode.objects.create(program=program, owner=owner, code="AMBV51")
    invite = ReferralInvite.objects.create(code=code, landing_path="/catalog", click_session_key="session-v51")
    attribution = ReferralEngine.bind_signup(invite=invite, referred_user=referred)

    first = ReferralRewardService.reward_for_paid_order(
        attribution=attribution,
        trigger_reference="order-v51-1",
        order_amount=Decimal("1000.00"),
    )
    second = ReferralRewardService.reward_for_paid_order(
        attribution=attribution,
        trigger_reference="order-v51-1",
        order_amount=Decimal("1000.00"),
    )

    invite.refresh_from_db()

    assert first.id == second.id
    assert invite.status == ReferralInvite.STATUS_CONVERTED
    assert ReferralReward.objects.filter(
        attribution=attribution,
        trigger_type=ReferralRewardService.TRIGGER_ORDER_PAID,
        trigger_reference="order-v51-1",
    ).count() == 1
    assert ReferralLedger.objects.filter(owner=owner, entry_type=ReferralLedger.ENTRY_REWARD).count() == 1
    assert ReferralLedger.objects.get(owner=owner).balance_after == Decimal("250.00")


@pytest.mark.django_db
def test_percent_referral_program_uses_paid_order_amount():
    User = get_user_model()
    owner = User.objects.create_user(email="percent-owner@example.com", password="strong-pass-123")
    referred = User.objects.create_user(email="percent-buyer@example.com", password="strong-pass-123")

    program = ReferralProgram.objects.create(
        slug="percent-v51",
        name="Percent v51",
        reward_kind="percent",
        reward_amount=Decimal("15.00"),
    )
    code = ReferralCode.objects.create(program=program, owner=owner, code="PCT15V51")
    invite = ReferralInvite.objects.create(code=code, landing_path="/catalog")
    attribution = ReferralEngine.bind_signup(invite=invite, referred_user=referred)

    reward = ReferralRewardService.reward_for_paid_order(
        attribution=attribution,
        trigger_reference="order-v51-percent",
        order_amount=Decimal("1000.00"),
    )

    assert reward.amount == Decimal("150.00")
    assert ReferralLedger.objects.get(owner=owner).balance_after == Decimal("150.00")
