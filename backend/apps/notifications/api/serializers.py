from rest_framework import serializers

from apps.notifications.models import (
    AdminAnnouncement,
    AudienceType,
    Notification,
    NotificationDelivery,
    NotificationPreference,
    NotificationTemplate,
)


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = [
            'id',
            'code',
            'title_template',
            'channel',
            'notification_type',
            'subject_template',
            'body_template',
            'is_active',
            'created_at',
            'updated_at',
        ]


class NotificationDeliverySerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = NotificationDelivery
        fields = [
            'id',
            'user',
            'user_email',
            'channel',
            'type',
            'template_code',
            'subject',
            'status',
            'error_message',
            'provider',
            'provider_message_id',
            'sent_at',
            'created_at',
        ]


class NotificationSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='notification_uuid', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'channel',
            'title',
            'body',
            'cta_label',
            'cta_url',
            'metadata',
            'status',
            'is_read',
            'read_at',
            'sent_at',
            'created_at',
        ]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            'in_app_enabled',
            'email_enabled',
            'marketing_enabled',
            'product_updates_enabled',
            'quiet_hours_start',
            'quiet_hours_end',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class AdminAnnouncementSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='announcement_uuid', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    notifications_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = AdminAnnouncement
        fields = [
            'id',
            'title',
            'body',
            'cta_label',
            'cta_url',
            'audience_type',
            'starts_at',
            'ends_at',
            'is_published',
            'published_at',
            'created_at',
            'updated_at',
            'created_by_email',
            'notifications_count',
        ]


class AdminAnnouncementCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    body = serializers.CharField()
    cta_label = serializers.CharField(max_length=100, required=False, allow_blank=True)
    cta_url = serializers.CharField(max_length=500, required=False, allow_blank=True)
    audience_type = serializers.ChoiceField(choices=AudienceType.choices, default=AudienceType.ALL_USERS)
    starts_at = serializers.DateTimeField(required=False, allow_null=True)
    ends_at = serializers.DateTimeField(required=False, allow_null=True)
    publish_now = serializers.BooleanField(default=False)
    user_ids = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)

    def validate(self, attrs):
        if attrs.get('audience_type') == AudienceType.SPECIFIC_USERS and not attrs.get('user_ids'):
            raise serializers.ValidationError({'user_ids': 'user_ids is required for specific_users announcements.'})
        if attrs.get('ends_at') and attrs.get('starts_at') and attrs['ends_at'] <= attrs['starts_at']:
            raise serializers.ValidationError({'ends_at': 'ends_at must be later than starts_at.'})
        return attrs


class NotificationProjectionRunSerializer(serializers.Serializer):
    batch_size = serializers.IntegerField(required=False, min_value=1, max_value=500, default=100)


class NotificationProjectionHealthSerializer(serializers.Serializer):
    consumer = serializers.CharField()
    status = serializers.CharField()
    projected_messages = serializers.IntegerField()
    skipped_messages = serializers.IntegerField()
    failed_messages = serializers.IntegerField()
    created_notifications = serializers.IntegerField()
    latest_processed_at = serializers.DateTimeField(allow_null=True)
    latest_message_key = serializers.CharField(allow_blank=True)
    latest_payload = serializers.DictField()
    notification_counts = serializers.ListField(child=serializers.DictField())
