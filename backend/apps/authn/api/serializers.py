from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=['user', 'trainer'], required=False, default='user')
    full_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate(self, attrs):
        full_name = (attrs.get('full_name') or '').strip()
        first_name = (attrs.get('first_name') or '').strip()
        last_name = (attrs.get('last_name') or '').strip()
        if not full_name and not first_name and not last_name:
            attrs['full_name'] = attrs['email'].split('@', 1)[0]
        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class RefreshSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=False, allow_blank=True)


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=False, allow_blank=True)


class AuthSettingsSerializer(serializers.Serializer):
    marketing_emails_enabled = serializers.BooleanField(required=False)
    product_updates_enabled = serializers.BooleanField(required=False)
    push_notifications_enabled = serializers.BooleanField(required=False)
    favorite_categories = serializers.ListField(child=serializers.CharField(), required=False)


class AuthUserSerializer(serializers.Serializer):
    id = serializers.CharField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    display_name = serializers.CharField(allow_blank=True, required=False)
    phone = serializers.CharField(allow_blank=True, required=False)
    country = serializers.CharField(allow_blank=True, required=False)
    city = serializers.CharField(allow_blank=True, required=False)
    timezone = serializers.CharField(required=False)
    preferred_language = serializers.CharField(required=False)
    active_role = serializers.CharField()
    available_roles = serializers.ListField(child=serializers.CharField())
    is_staff = serializers.BooleanField(required=False)
    is_superuser = serializers.BooleanField(required=False)
    settings = AuthSettingsSerializer(required=False)
    access_token = serializers.CharField(required=False)
    refresh_token = serializers.CharField(required=False)


class SessionSerializer(serializers.Serializer):
    is_authenticated = serializers.BooleanField()
    user = AuthUserSerializer(allow_null=True)


class TokenPairSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
