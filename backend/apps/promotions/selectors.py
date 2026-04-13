from django.db.models import Count
from django.utils import timezone

from apps.promotions.models import PromoCampaign, PromoCode, PromoCampaignStatus


class PromoSelector:
    @staticmethod
    def get_active_code_or_none(code: str):
        normalized = code.strip().upper()
        now = timezone.now()
        return (
            PromoCode.objects.select_related("campaign", "campaign__trainer")
            .filter(
                code=normalized,
                is_active=True,
                campaign__status=PromoCampaignStatus.ACTIVE,
                campaign__starts_at__lte=now,
            )
            .filter(campaign__ends_at__isnull=True)
            .first()
            or PromoCode.objects.select_related("campaign", "campaign__trainer")
            .filter(
                code=normalized,
                is_active=True,
                campaign__status=PromoCampaignStatus.ACTIVE,
                campaign__starts_at__lte=now,
                campaign__ends_at__gt=now,
            )
            .first()
        )

    @staticmethod
    def trainer_campaigns_with_stats(trainer):
        return (
            PromoCampaign.objects.filter(trainer=trainer)
            .annotate(redemptions_count=Count("redemptions"))
            .order_by("-created_at")
        )
