from decimal import Decimal

from apps.promotions.services import PromoService


class OrderDraftPromoApplicator:
    @staticmethod
    def apply(*, user, draft, promo_code: str | None):
        draft.promo_code = None
        draft.discount_amount = Decimal("0.00")
        draft.discount_funded_by_platform_amount = Decimal("0.00")
        draft.discount_funded_by_trainer_amount = Decimal("0.00")
        draft.total_amount = draft.subtotal_amount

        if not promo_code:
            return draft

        result = PromoService.validate_and_price(
            user=user,
            subtotal_amount=draft.subtotal_amount,
            promo_code=promo_code,
        )

        draft.promo_code = result.code
        draft.discount_amount = result.discount_amount
        draft.discount_funded_by_platform_amount = result.funded_by_platform_amount
        draft.discount_funded_by_trainer_amount = result.funded_by_trainer_amount
        draft.total_amount = result.payable_total_amount
        draft.promo_campaign_id = result.campaign_id
        draft.promo_code_id = result.promo_code_id
        return draft


def apply_promo_code_to_order_draft(*, user, draft, promo_code: str | None):
    return OrderDraftPromoApplicator.apply(user=user, draft=draft, promo_code=promo_code)
