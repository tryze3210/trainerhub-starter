from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.affiliates.models import (
    AffiliateAttribution,
    AffiliateClick,
    AffiliateCommission,
    AffiliateCommissionStatus,
    CommissionKind,
    OrderAttribution,
)
from apps.affiliates.selectors import AffiliateSelector

TWOPLACES = Decimal("0.01")


@dataclass
class ClickCaptureResult:
    partner_id: int
    click_id: int
    attribution_id: int


class AffiliateTrackingService:
    @staticmethod
    @transaction.atomic
    def capture_click(*, partner_code: str, client_key: str, landing_path: str = "", referrer_url: str = "", utm: dict | None = None, user=None, ip_address=None, user_agent: str = "") -> ClickCaptureResult:
        partner = AffiliateSelector.get_active_partner_by_code_or_none(partner_code)
        if not partner:
            raise ValidationError("Affiliate partner is invalid or inactive")

        utm = utm or {}
        click = AffiliateClick.objects.create(
            partner=partner,
            landing_path=landing_path,
            referrer_url=referrer_url or "",
            utm_source=utm.get("utm_source", ""),
            utm_medium=utm.get("utm_medium", ""),
            utm_campaign=utm.get("utm_campaign", ""),
            utm_content=utm.get("utm_content", ""),
            utm_term=utm.get("utm_term", ""),
            client_key=client_key,
            user=user if getattr(user, "is_authenticated", False) else None,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        AffiliateAttribution.objects.filter(client_key=client_key, is_active=True).update(is_active=False)
        if getattr(user, "is_authenticated", False):
            AffiliateAttribution.objects.filter(user=user, is_active=True).update(is_active=False)

        expires_at = timezone.now() + timezone.timedelta(days=partner.cookie_ttl_days)
        attribution = AffiliateAttribution.objects.create(
            partner=partner,
            click=click,
            user=user if getattr(user, "is_authenticated", False) else None,
            client_key=client_key,
            expires_at=expires_at,
            snapshot={
                "partner_code": partner.code,
                "attribution_model": partner.attribution_model,
                "utm": utm,
            },
        )
        return ClickCaptureResult(partner_id=partner.id, click_id=click.id, attribution_id=attribution.id)


class AffiliateCommissionService:
    @staticmethod
    def _calculate_commission_amount(*, partner, commission_base_amount: Decimal) -> Decimal:
        if partner.commission_kind == CommissionKind.FIXED:
            return min(partner.commission_value, commission_base_amount).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        return (commission_base_amount * partner.commission_value / Decimal("100.00")).quantize(TWOPLACES, rounding=ROUND_HALF_UP)

    @staticmethod
    @transaction.atomic
    def attribute_order(*, order, user=None, client_key: str | None = None):
        attribution = AffiliateSelector.get_active_attribution_for_subject(user=user, client_key=client_key)
        if not attribution:
            return None

        partner = attribution.partner
        order_user_id = getattr(order, "user_id", None)
        if order_user_id and attribution.partner.user_id == order_user_id and not partner.allow_self_referrals:
            return None

        if hasattr(order, "subtotal_amount"):
            commission_base_amount = order.subtotal_amount
        elif hasattr(order, "paid_amount"):
            commission_base_amount = order.paid_amount
        else:
            raise ValidationError("Order must expose subtotal_amount or paid_amount for affiliate attribution")

        commission_amount = AffiliateCommissionService._calculate_commission_amount(
            partner=partner,
            commission_base_amount=commission_base_amount,
        )

        order_attr = OrderAttribution.objects.create(
            order=order,
            partner=partner,
            click=attribution.click,
            attributed_user=user if getattr(user, "is_authenticated", False) else None,
            attribution_model=partner.attribution_model,
            commission_base_amount=commission_base_amount,
            commission_amount=commission_amount,
            currency=getattr(order, "currency", "RUB"),
            utm_snapshot=attribution.snapshot.get("utm", {}),
            click_snapshot={
                "landing_path": attribution.click.landing_path if attribution.click else "",
                "clicked_at": attribution.click.clicked_at.isoformat() if attribution.click else None,
            },
        )
        commission = AffiliateCommission.objects.create(
            order_attribution=order_attr,
            partner=partner,
            order=order,
            amount=commission_amount,
            currency=order_attr.currency,
        )
        return commission

    @staticmethod
    def approve_commission(*, commission: AffiliateCommission):
        commission.status = AffiliateCommissionStatus.APPROVED
        commission.approved_at = timezone.now()
        commission.save(update_fields=["status", "approved_at"])
        return commission

    @staticmethod
    def reverse_commission(*, commission: AffiliateCommission):
        if commission.status == AffiliateCommissionStatus.REVERSED:
            return commission
        commission.status = AffiliateCommissionStatus.REVERSED
        commission.reversed_at = timezone.now()
        commission.save(update_fields=["status", "reversed_at"])
        return commission
