from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError

from apps.promotions.models import DiscountFundingSource, DiscountType, PromoRedemption
from apps.promotions.selectors import PromoSelector


TWOPLACES = Decimal("0.01")


@dataclass
class PromoPricingResult:
    code: str
    subtotal_amount: Decimal
    discount_amount: Decimal
    funded_by_platform_amount: Decimal
    funded_by_trainer_amount: Decimal
    payable_total_amount: Decimal
    campaign_id: int
    promo_code_id: int


class PromoService:
    @staticmethod
    def validate_and_price(*, user, subtotal_amount: Decimal, promo_code: str) -> PromoPricingResult:
        promo = PromoSelector.get_active_code_or_none(promo_code)
        if not promo:
            raise ValidationError("Promo code is invalid or inactive")

        campaign = promo.campaign

        if promo.min_order_amount and subtotal_amount < promo.min_order_amount:
            raise ValidationError("Order amount does not meet minimum threshold")

        user_redemptions_count = PromoRedemption.objects.filter(code=promo, user=user).count()
        if campaign.max_redemptions_per_user and user_redemptions_count >= campaign.max_redemptions_per_user:
            raise ValidationError("Promo code usage limit reached for user")

        total_redemptions_count = PromoRedemption.objects.filter(campaign=campaign).count()
        if campaign.max_redemptions_total and total_redemptions_count >= campaign.max_redemptions_total:
            raise ValidationError("Promo campaign exhausted")

        if promo.discount_type == DiscountType.FIXED:
            discount_amount = min(promo.discount_value, subtotal_amount)
        else:
            discount_amount = (subtotal_amount * promo.discount_value / Decimal("100.00")).quantize(
                TWOPLACES, rounding=ROUND_HALF_UP
            )

        if promo.max_discount_amount:
            discount_amount = min(discount_amount, promo.max_discount_amount)

        if campaign.funding_source == DiscountFundingSource.PLATFORM:
            funded_by_platform_amount = discount_amount
            funded_by_trainer_amount = Decimal("0.00")
        elif campaign.funding_source == DiscountFundingSource.TRAINER:
            funded_by_platform_amount = Decimal("0.00")
            funded_by_trainer_amount = discount_amount
        else:
            funded_by_platform_amount = (discount_amount * campaign.shared_platform_ratio).quantize(
                TWOPLACES, rounding=ROUND_HALF_UP
            )
            funded_by_trainer_amount = discount_amount - funded_by_platform_amount

        payable_total_amount = subtotal_amount - discount_amount

        return PromoPricingResult(
            code=promo.code,
            subtotal_amount=subtotal_amount,
            discount_amount=discount_amount,
            funded_by_platform_amount=funded_by_platform_amount,
            funded_by_trainer_amount=funded_by_trainer_amount,
            payable_total_amount=payable_total_amount,
            campaign_id=campaign.id,
            promo_code_id=promo.id,
        )
