from rest_framework import serializers

from apps.promotions.models import PromoCampaign, PromoCode


class PromoCampaignSerializer(serializers.ModelSerializer):
    redemptions_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = PromoCampaign
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "status",
            "funding_source",
            "shared_platform_ratio",
            "trainer",
            "starts_at",
            "ends_at",
            "max_redemptions_total",
            "max_redemptions_per_user",
            "is_first_order_only",
            "is_new_customer_only",
            "redemptions_count",
            "created_at",
            "updated_at",
        ]


class PromoCodeSerializer(serializers.ModelSerializer):
    campaign_name = serializers.CharField(source="campaign.name", read_only=True)

    class Meta:
        model = PromoCode
        fields = [
            "id",
            "campaign",
            "campaign_name",
            "code",
            "discount_type",
            "discount_value",
            "min_order_amount",
            "max_discount_amount",
            "is_active",
            "created_at",
        ]
