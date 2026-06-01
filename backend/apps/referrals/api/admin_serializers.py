from __future__ import annotations

from rest_framework import serializers

from apps.referrals.models import ReferralAttribution, ReferralInvite, ReferralLedger, ReferralReward


class AdminReferralInviteSerializer(serializers.ModelSerializer):
    code_value = serializers.CharField(source="code.code", read_only=True)
    program_id = serializers.UUIDField(source="code.program_id", read_only=True)
    program_slug = serializers.CharField(source="code.program.slug", read_only=True)
    owner_id = serializers.UUIDField(source="code.owner_id", read_only=True)
    owner_email = serializers.EmailField(source="code.owner.email", read_only=True)
    referred_user_id = serializers.SerializerMethodField()
    referred_user_email = serializers.SerializerMethodField()
    attribution_id = serializers.SerializerMethodField()

    class Meta:
        model = ReferralInvite
        fields = [
            "id",
            "code_value",
            "program_id",
            "program_slug",
            "owner_id",
            "owner_email",
            "landing_path",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "click_session_key",
            "status",
            "expires_at",
            "converted_at",
            "created_at",
            "attribution_id",
            "referred_user_id",
            "referred_user_email",
        ]

    def _attribution(self, obj: ReferralInvite) -> ReferralAttribution | None:
        try:
            return obj.attribution
        except ReferralAttribution.DoesNotExist:
            return None

    def get_attribution_id(self, obj: ReferralInvite) -> str | None:
        attribution = self._attribution(obj)
        return str(attribution.id) if attribution else None

    def get_referred_user_id(self, obj: ReferralInvite) -> str | None:
        attribution = self._attribution(obj)
        return str(attribution.referred_user_id) if attribution else None

    def get_referred_user_email(self, obj: ReferralInvite) -> str:
        attribution = self._attribution(obj)
        referred_user = getattr(attribution, "referred_user", None) if attribution else None
        return getattr(referred_user, "email", "") if referred_user else ""


class AdminReferralAttributionSerializer(serializers.ModelSerializer):
    invite_id = serializers.UUIDField(read_only=True)
    referred_user_id = serializers.UUIDField(read_only=True)
    referred_user_email = serializers.EmailField(source="referred_user.email", read_only=True)
    owner_id = serializers.UUIDField(source="invite.code.owner_id", read_only=True)
    owner_email = serializers.EmailField(source="invite.code.owner.email", read_only=True)
    code_value = serializers.CharField(source="invite.code.code", read_only=True)
    program_slug = serializers.CharField(source="invite.code.program.slug", read_only=True)
    invite_status = serializers.CharField(source="invite.status", read_only=True)

    class Meta:
        model = ReferralAttribution
        fields = [
            "id",
            "invite_id",
            "referred_user_id",
            "referred_user_email",
            "owner_id",
            "owner_email",
            "code_value",
            "program_slug",
            "invite_status",
            "attribution_model",
            "is_locked",
            "created_at",
        ]


class AdminReferralRewardSerializer(serializers.ModelSerializer):
    attribution_id = serializers.UUIDField(read_only=True)
    invite_id = serializers.UUIDField(source="attribution.invite_id", read_only=True)
    referred_user_id = serializers.UUIDField(source="attribution.referred_user_id", read_only=True)
    referred_user_email = serializers.EmailField(source="attribution.referred_user.email", read_only=True)
    owner_id = serializers.UUIDField(source="attribution.invite.code.owner_id", read_only=True)
    owner_email = serializers.EmailField(source="attribution.invite.code.owner.email", read_only=True)
    code_value = serializers.CharField(source="attribution.invite.code.code", read_only=True)
    program_slug = serializers.CharField(source="attribution.invite.code.program.slug", read_only=True)
    ledger_entry_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ReferralReward
        fields = [
            "id",
            "attribution_id",
            "invite_id",
            "referred_user_id",
            "referred_user_email",
            "owner_id",
            "owner_email",
            "code_value",
            "program_slug",
            "trigger_type",
            "trigger_reference",
            "amount",
            "status",
            "ledger_entry_count",
            "created_at",
        ]


class AdminReferralLedgerSerializer(serializers.ModelSerializer):
    owner_id = serializers.UUIDField(read_only=True)
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    reward_id = serializers.UUIDField(read_only=True)
    reward_status = serializers.CharField(source="reward.status", read_only=True)
    reward_trigger_type = serializers.CharField(source="reward.trigger_type", read_only=True)
    reward_trigger_reference = serializers.CharField(source="reward.trigger_reference", read_only=True)
    referred_user_id = serializers.SerializerMethodField()
    referred_user_email = serializers.SerializerMethodField()
    program_slug = serializers.SerializerMethodField()

    class Meta:
        model = ReferralLedger
        fields = [
            "id",
            "owner_id",
            "owner_email",
            "reward_id",
            "reward_status",
            "reward_trigger_type",
            "reward_trigger_reference",
            "referred_user_id",
            "referred_user_email",
            "program_slug",
            "entry_type",
            "amount",
            "balance_after",
            "created_at",
        ]

    def _attribution(self, obj: ReferralLedger) -> ReferralAttribution | None:
        reward = getattr(obj, "reward", None)
        return getattr(reward, "attribution", None) if reward else None

    def get_referred_user_id(self, obj: ReferralLedger) -> str | None:
        attribution = self._attribution(obj)
        return str(attribution.referred_user_id) if attribution else None

    def get_referred_user_email(self, obj: ReferralLedger) -> str:
        attribution = self._attribution(obj)
        referred_user = getattr(attribution, "referred_user", None) if attribution else None
        return getattr(referred_user, "email", "") if referred_user else ""

    def get_program_slug(self, obj: ReferralLedger) -> str:
        attribution = self._attribution(obj)
        if not attribution:
            return ""
        return attribution.invite.code.program.slug
