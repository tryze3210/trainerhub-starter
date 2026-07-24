from rest_framework import serializers

from apps.affiliates.models import AffiliateClick, AffiliateCommission, AffiliatePartner, OrderAttribution


class AffiliatePartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AffiliatePartner
        fields = [
            "id",
            "display_name",
            "code",
            "status",
            "commission_kind",
            "commission_value",
            "attribution_model",
            "cookie_ttl_days",
            "allow_self_referrals",
            "trainer_id",
            "created_at",
        ]


class AffiliateClickSerializer(serializers.ModelSerializer):
    partner = AffiliatePartnerSerializer(read_only=True)

    class Meta:
        model = AffiliateClick
        fields = [
            "id",
            "partner",
            "landing_path",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "clicked_at",
        ]


class OrderAttributionSerializer(serializers.ModelSerializer):
    partner = AffiliatePartnerSerializer(read_only=True)

    class Meta:
        model = OrderAttribution
        fields = [
            "id",
            "order_id",
            "partner",
            "attribution_model",
            "commission_base_amount",
            "commission_amount",
            "currency",
            "utm_snapshot",
            "click_snapshot",
            "created_at",
        ]


class AffiliateCommissionSerializer(serializers.ModelSerializer):
    partner = AffiliatePartnerSerializer(read_only=True)
    order_attribution = OrderAttributionSerializer(read_only=True)

    class Meta:
        model = AffiliateCommission
        fields = [
            "id",
            "partner",
            "order_id",
            "amount",
            "currency",
            "status",
            "approved_at",
            "paid_out_at",
            "reversed_at",
            "order_attribution",
            "created_at",
        ]


class AffiliateClickCaptureSerializer(serializers.Serializer):
    partner_code = serializers.CharField(max_length=64)
    client_key = serializers.CharField(max_length=128)
    landing_path = serializers.CharField(max_length=512, required=False, allow_blank=True)
    referrer_url = serializers.CharField(max_length=1024, required=False, allow_blank=True)
    utm = serializers.DictField(required=False)
