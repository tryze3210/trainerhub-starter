from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from django.conf import settings


MONEY_QUANT = Decimal('0.01')
RATE_QUANT = Decimal('0.0001')


@dataclass(frozen=True)
class CommissionSplit:
    gross_amount: Decimal
    platform_commission: Decimal
    trainer_net: Decimal
    rate: Decimal
    rate_percent: Decimal
    currency: str

    def as_snapshot(self, *, source: str) -> dict[str, str]:
        return {
            'rate': str(self.rate),
            'rate_percent': str(self.rate_percent),
            'currency': self.currency,
            'gross_amount': str(self.gross_amount),
            'platform_commission': str(self.platform_commission),
            'trainer_net': str(self.trainer_net),
            'source': source,
        }


class CommissionPolicyService:
    """Single source of truth for platform commission math."""

    DEFAULT_RATE_PERCENT = Decimal('20.00')

    @classmethod
    def _decimal(cls, value: Any, *, default: Decimal = Decimal('0.00'), quant: Decimal = MONEY_QUANT) -> Decimal:
        if value is None or value == '':
            return default.quantize(quant)
        try:
            return Decimal(str(value)).quantize(quant)
        except (InvalidOperation, TypeError, ValueError):
            return default.quantize(quant)

    @classmethod
    def rate(cls) -> Decimal:
        raw = getattr(settings, 'GLOBAL_COMMISSION_RATE', None)
        if raw is None:
            raw = getattr(settings, 'PLATFORM_COMMISSION_RATE', None)
        rate = cls._decimal(raw, default=cls.DEFAULT_RATE_PERCENT, quant=RATE_QUANT)
        if rate > Decimal('1.00'):
            rate = (rate / Decimal('100')).quantize(RATE_QUANT)
        return min(max(rate, Decimal('0.0000')), Decimal('1.0000'))

    @classmethod
    def split(cls, *, gross_amount: Decimal, currency: str = 'RUB') -> CommissionSplit:
        gross = cls._decimal(gross_amount)
        rate = cls.rate()
        platform_commission = (gross * rate).quantize(MONEY_QUANT)
        trainer_net = (gross - platform_commission).quantize(MONEY_QUANT)
        return CommissionSplit(
            gross_amount=gross,
            platform_commission=platform_commission,
            trainer_net=trainer_net,
            rate=rate,
            rate_percent=(rate * Decimal('100')).quantize(MONEY_QUANT),
            currency=currency,
        )

    @classmethod
    def gross_from_net(cls, *, net_amount: Decimal) -> Decimal:
        net = cls._decimal(net_amount)
        payout_ratio = Decimal('1.0000') - cls.rate()
        if payout_ratio <= Decimal('0.0000'):
            return net
        return (net / payout_ratio).quantize(MONEY_QUANT)
