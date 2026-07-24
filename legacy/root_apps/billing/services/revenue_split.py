from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from apps.billing.models import TrainerRevenuePolicy


TWOPLACES = Decimal("0.01")


@dataclass(frozen=True)
class RevenueSplitResult:
    gross_amount: Decimal
    trainer_amount: Decimal
    platform_amount: Decimal
    trainer_share_percent: Decimal
    platform_commission_percent: Decimal


class RevenuePolicyNotFound(Exception):
    pass


class InvalidRevenuePolicy(Exception):
    pass


class RevenueSplitService:
    @staticmethod
    def quantize(value: Decimal) -> Decimal:
        return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)

    @classmethod
    def resolve_policy(
        cls,
        *,
        trainer,
        order_item_type: Optional[str] = None,
        subscription_plan_code: Optional[str] = None,
    ) -> TrainerRevenuePolicy:
        queryset = TrainerRevenuePolicy.objects.filter(trainer=trainer, is_active=True)

        if subscription_plan_code:
            policy = queryset.filter(subscription_plan_code=subscription_plan_code).order_by("priority", "-effective_from").first()
            if policy:
                return policy

        if order_item_type:
            policy = queryset.filter(order_item_type=order_item_type).order_by("priority", "-effective_from").first()
            if policy:
                return policy

        policy = queryset.order_by("priority", "-effective_from").first()
        if not policy:
            raise RevenuePolicyNotFound(f"No active revenue policy found for trainer_id={trainer.id}")
        return policy

    @classmethod
    def calculate(
        cls,
        *,
        gross_amount: Decimal,
        trainer,
        order_item_type: Optional[str] = None,
        subscription_plan_code: Optional[str] = None,
    ) -> RevenueSplitResult:
        policy = cls.resolve_policy(
            trainer=trainer,
            order_item_type=order_item_type,
            subscription_plan_code=subscription_plan_code,
        )

        total_percent = policy.trainer_share_percent + policy.platform_commission_percent
        if total_percent != Decimal("100.00"):
            raise InvalidRevenuePolicy(
                f"Revenue policy must sum to 100.00, got {total_percent} for policy_id={policy.id}"
            )

        trainer_amount = cls.quantize(gross_amount * policy.trainer_share_percent / Decimal("100.00"))
        platform_amount = cls.quantize(gross_amount - trainer_amount)

        return RevenueSplitResult(
            gross_amount=cls.quantize(gross_amount),
            trainer_amount=trainer_amount,
            platform_amount=platform_amount,
            trainer_share_percent=policy.trainer_share_percent,
            platform_commission_percent=policy.platform_commission_percent,
        )
