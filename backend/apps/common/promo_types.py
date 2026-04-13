from dataclasses import dataclass
from decimal import Decimal


@dataclass
class OrderDraftPricingSnapshot:
    subtotal_amount: Decimal
    discount_amount: Decimal = Decimal("0.00")
    discount_funded_by_platform_amount: Decimal = Decimal("0.00")
    discount_funded_by_trainer_amount: Decimal = Decimal("0.00")
    total_amount: Decimal = Decimal("0.00")
    promo_code: str | None = None
    promo_campaign_id: int | None = None
    promo_code_id: int | None = None
