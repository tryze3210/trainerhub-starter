from django.utils import timezone

from apps.affiliates.models import AffiliateAttribution, AffiliatePartner, AffiliatePartnerStatus


class AffiliateSelector:
    @staticmethod
    def get_active_partner_by_code_or_none(code: str):
        normalized = code.strip().upper()
        return (
            AffiliatePartner.objects.filter(code=normalized, status=AffiliatePartnerStatus.ACTIVE)
            .select_related("trainer", "user")
            .first()
        )

    @staticmethod
    def get_active_attribution_for_subject(*, user=None, client_key: str | None = None):
        now = timezone.now()
        qs = AffiliateAttribution.objects.filter(is_active=True, expires_at__gt=now).select_related("partner", "click")
        if user is not None:
            attribution = qs.filter(user=user).order_by("-attributed_at").first()
            if attribution:
                return attribution
        if client_key:
            return qs.filter(client_key=client_key).order_by("-attributed_at").first()
        return None
