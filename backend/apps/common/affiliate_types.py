from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class AffiliateContext:
    partner_code: str
    client_key: str
    utm_source: str = ""
    utm_medium: str = ""
    utm_campaign: str = ""
    utm_content: str = ""
    utm_term: str = ""


@dataclass(frozen=True)
class AffiliateCommissionPreview:
    partner_id: int
    commission_base_amount: Decimal
    commission_amount: Decimal
    currency: str
