from rest_framework import serializers

from apps.referrals.models import ReferralCode, ReferralInvite, ReferralLedger, ReferralProgram


class ReferralProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralProgram
        fields = [
            "id",
            "slug",
            "name",
            "is_active",
            "reward_kind",
            "reward_amount",
            "invite_ttl_days",
        ]


class ReferralCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralCode
        fields = ["id", "program", "code", "is_active", "created_at"]


class ReferralInviteSerializer(serializers.ModelSerializer):
    code_value = serializers.CharField(source="code.code", read_only=True)

    class Meta:
        model = ReferralInvite
        fields = [
            "id",
            "code_value",
            "landing_path",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "status",
            "created_at",
            "converted_at",
        ]


class ReferralLedgerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralLedger
        fields = ["id", "entry_type", "amount", "balance_after", "created_at"]


class TrackReferralSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=64)
    landing_path = serializers.CharField(max_length=255, required=False, allow_blank=True)
    utm_source = serializers.CharField(max_length=128, required=False, allow_blank=True)
    utm_medium = serializers.CharField(max_length=128, required=False, allow_blank=True)
    utm_campaign = serializers.CharField(max_length=128, required=False, allow_blank=True)
    click_session_key = serializers.CharField(max_length=128, required=False, allow_blank=True)


class GenerateCodeSerializer(serializers.Serializer):
    program_slug = serializers.SlugField()
