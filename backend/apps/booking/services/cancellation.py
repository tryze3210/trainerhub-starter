from dataclasses import dataclass
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone


@dataclass
class CancellationQuote:
    refund_percent: int
    refund_amount: Decimal
    window: str


class CancellationPolicyService:
    def quote_refund(self, reservation, policy, amount: Decimal) -> CancellationQuote:
        delta = reservation.starts_at - timezone.now()
        if delta >= timedelta(hours=24):
            percent = policy.refund_percent_before_24h
            window = ">=24h"
        elif delta >= timedelta(hours=3):
            percent = policy.refund_percent_before_3h
            window = "3h-24h"
        else:
            percent = policy.refund_percent_after_window
            window = "<3h"
        refund_amount = (amount * Decimal(percent) / Decimal("100")).quantize(Decimal("0.01"))
        return CancellationQuote(refund_percent=percent, refund_amount=refund_amount, window=window)
