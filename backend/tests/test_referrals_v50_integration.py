from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model

from apps.authn.services import register_user
from apps.referrals.models import ReferralAttribution, ReferralCode, ReferralInvite, ReferralLedger, ReferralProgram, ReferralReward
from apps.referrals.services.integration import ReferralIntegrationService


@pytest.mark.django_db
def test_register_user_binds_referral_invite_and_paid_order_reward_is_idempotent():
    User = get_user_model()
    owner = User.objects.create_user(email='trainer-owner@example.com', password='strong-pass-123')

    program = ReferralProgram.objects.create(
        slug='ambassador',
        name='Ambassador program',
        reward_kind='fixed',
        reward_amount=Decimal('250.00'),
    )
    code = ReferralCode.objects.create(program=program, owner=owner, code='AMB250')
    invite = ReferralInvite.objects.create(code=code, landing_path='/catalog', click_session_key='session-1')

    register_user(
        email='buyer@example.com',
        password='strong-pass-123',
        full_name='Buyer Example',
        referral_invite_id=str(invite.id),
    )

    buyer = User.objects.get(email='buyer@example.com')
    attribution = ReferralAttribution.objects.get(referred_user=buyer)
    assert attribution.invite_id == invite.id

    order_stub = SimpleNamespace(id=uuid4(), user=buyer)
    reward = ReferralIntegrationService.reward_for_paid_order_if_eligible(order=order_stub)
    duplicate_reward = ReferralIntegrationService.reward_for_paid_order_if_eligible(order=order_stub)

    assert reward.id == duplicate_reward.id
    assert reward.amount == Decimal('250.00')
    assert ReferralReward.objects.filter(attribution=attribution, trigger_reference=str(order_stub.id)).count() == 1
    assert ReferralLedger.objects.filter(owner=owner, reward=reward).count() == 1

    invite.refresh_from_db()
    assert invite.status == ReferralInvite.STATUS_CONVERTED
    assert invite.converted_at is not None
