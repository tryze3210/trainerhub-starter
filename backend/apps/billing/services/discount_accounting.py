"""
Интеграционный слой для v21 payout ledger / revenue split.

Ожидаемая идея:
- после финализации order у нас уже есть order gross/subtotal/discount/net payable;
- если discount funded by platform -> это platform marketing subsidy expense;
- если discount funded by trainer -> уменьшаем trainer revenue basis;
- если shared -> делим impact.
"""

from decimal import Decimal

from apps.promotions.models import PromoRedemption


class DiscountAccountingService:
    @staticmethod
    def record_discount_financial_impact(*, order):
        if not getattr(order, "promo_code_id", None):
            return None

        # Здесь предполагается существующий ledger service из v21.
        # Замени import / сигнатуры на свои реальные.
        from apps.billing.services.ledger import LedgerService

        subtotal_amount = order.subtotal_amount
        discount_amount = order.discount_amount
        funded_by_platform_amount = getattr(order, "discount_funded_by_platform_amount", Decimal("0.00"))
        funded_by_trainer_amount = getattr(order, "discount_funded_by_trainer_amount", Decimal("0.00"))

        PromoRedemption.objects.get_or_create(
            code_id=order.promo_code_id,
            campaign_id=order.promo_campaign_id,
            user=order.user,
            order=order,
            defaults={
                "currency": order.currency,
                "subtotal_amount": subtotal_amount,
                "discount_amount": discount_amount,
                "funded_by_platform_amount": funded_by_platform_amount,
                "funded_by_trainer_amount": funded_by_trainer_amount,
            },
        )

        if funded_by_platform_amount > 0:
            LedgerService.create_entry(
                owner_type="platform",
                entry_type="promo_subsidy_expense",
                amount=funded_by_platform_amount,
                currency=order.currency,
                reference=str(order.pk),
                metadata={
                    "order_id": order.pk,
                    "promo_code_id": order.promo_code_id,
                    "promo_campaign_id": order.promo_campaign_id,
                },
            )

        if funded_by_trainer_amount > 0:
            LedgerService.create_entry(
                owner_type="trainer",
                owner_id=order.trainer_id,
                entry_type="promo_discount_trainer_contra_revenue",
                amount=funded_by_trainer_amount,
                currency=order.currency,
                reference=str(order.pk),
                metadata={
                    "order_id": order.pk,
                    "promo_code_id": order.promo_code_id,
                    "promo_campaign_id": order.promo_campaign_id,
                },
            )

        return True

    @staticmethod
    def reverse_discount_financial_impact(*, order, refund):
        if not getattr(order, "promo_code_id", None):
            return None

        from apps.billing.services.ledger import LedgerService

        funded_by_platform_amount = getattr(order, "discount_funded_by_platform_amount", Decimal("0.00"))
        funded_by_trainer_amount = getattr(order, "discount_funded_by_trainer_amount", Decimal("0.00"))

        if funded_by_platform_amount > 0:
            LedgerService.create_entry(
                owner_type="platform",
                entry_type="promo_subsidy_expense_reversal",
                amount=funded_by_platform_amount,
                currency=order.currency,
                reference=str(refund.pk),
                metadata={"order_id": order.pk, "refund_id": refund.pk},
            )

        if funded_by_trainer_amount > 0:
            LedgerService.create_entry(
                owner_type="trainer",
                owner_id=order.trainer_id,
                entry_type="promo_discount_trainer_contra_revenue_reversal",
                amount=funded_by_trainer_amount,
                currency=order.currency,
                reference=str(refund.pk),
                metadata={"order_id": order.pk, "refund_id": refund.pk},
            )

        return True


def record_discount_financial_impact(*, order):
    return DiscountAccountingService.record_discount_financial_impact(order=order)
