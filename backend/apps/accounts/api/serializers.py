from rest_framework import serializers


class AccountProfileSerializer(serializers.Serializer):
    id = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    full_name = serializers.CharField()
    display_name = serializers.CharField(allow_blank=True)
    phone = serializers.CharField(allow_blank=True)
    country = serializers.CharField(allow_blank=True)
    city = serializers.CharField(allow_blank=True)
    timezone = serializers.CharField()
    preferred_language = serializers.CharField()
    active_role = serializers.CharField(required=False)
    available_roles = serializers.ListField(child=serializers.CharField(), required=False)
    trainer_slug = serializers.CharField(required=False)
    avatar_url = serializers.URLField(required=False)
    headline = serializers.CharField(required=False)
    bio = serializers.CharField(required=False)


class AccountSettingsSerializer(serializers.Serializer):
    marketing_emails_enabled = serializers.BooleanField()
    product_updates_enabled = serializers.BooleanField()
    push_notifications_enabled = serializers.BooleanField()
    favorite_categories = serializers.ListField(child=serializers.CharField())


class SwitchRoleSerializer(serializers.Serializer):
    role = serializers.CharField()


class SwitchRoleResponseSerializer(serializers.Serializer):
    active_role = serializers.CharField()
    available_roles = serializers.ListField(child=serializers.CharField())
    role_capabilities = serializers.ListField(child=serializers.CharField())


class QuickLinkSerializer(serializers.Serializer):
    label = serializers.CharField()
    href = serializers.CharField()


class CabinetStatsSerializer(serializers.Serializer):
    favorites_count = serializers.IntegerField()
    active_entitlements_count = serializers.IntegerField()
    draft_content_count = serializers.IntegerField()
    unread_notifications_count = serializers.IntegerField()


class CabinetSerializer(serializers.Serializer):
    account = AccountProfileSerializer()
    quick_links = QuickLinkSerializer(many=True)
    role_capabilities = serializers.ListField(child=serializers.CharField())
    stats = CabinetStatsSerializer()
