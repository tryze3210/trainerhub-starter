import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class NotificationChannel(models.TextChoices):
    IN_APP = 'in_app', 'In-app'
    EMAIL = 'email', 'Email'
    PUSH = 'push', 'Push'


class AudienceType(models.TextChoices):
    ALL_USERS = 'all_users', 'All users'
    ALL_TRAINERS = 'all_trainers', 'All trainers'
    SPECIFIC_USERS = 'specific_users', 'Specific users'


class DeliveryStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    SENT = 'sent', 'Sent'
    FAILED = 'failed', 'Failed'
    READ = 'read', 'Read'


class NotificationStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    SENT = 'sent', 'Sent'
    FAILED = 'failed', 'Failed'
    SKIPPED = 'skipped', 'Skipped'


class NotificationType:
    # Legacy notification categories used by notifications_notification.notification_type.
    SYSTEM = 'system'
    ORDER = 'order'
    PAYMENT = 'payment'
    SUBSCRIPTION = 'subscription'
    ANNOUNCEMENT = 'announcement'

    # Event-level types used by notifications_notificationdelivery.type.
    ORDER_PAID = 'order_paid'
    PAYMENT_FAILED = 'payment_failed'
    SUBSCRIPTION_ACTIVATED = 'subscription_activated'
    ADMIN_ANNOUNCEMENT = 'admin_announcement'

    LEGACY_CHOICES = [
        (SYSTEM, 'System'),
        (ORDER, 'Order'),
        (PAYMENT, 'Payment'),
        (SUBSCRIPTION, 'Subscription'),
        (ANNOUNCEMENT, 'Announcement'),
    ]

    DELIVERY_CHOICES = [
        (ORDER_PAID, 'Order paid'),
        (PAYMENT_FAILED, 'Payment failed'),
        (SUBSCRIPTION_ACTIVATED, 'Subscription activated'),
        (ADMIN_ANNOUNCEMENT, 'Admin announcement'),
    ]

    choices = LEGACY_CHOICES


class NotificationTemplate(models.Model):
    code = models.CharField(max_length=100, unique=True)
    title_template = models.CharField(max_length=255)
    subject_template = models.CharField(max_length=255, blank=True)
    body_template = models.TextField()
    notification_type = models.CharField(
        max_length=32,
        choices=NotificationType.LEGACY_CHOICES,
        default=NotificationType.SYSTEM,
    )
    channel = models.CharField(
        max_length=16,
        choices=NotificationChannel.choices,
        default=NotificationChannel.IN_APP,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notifications_template'
        ordering = ['code']

    def __str__(self):
        return f'{self.code}:{self.channel}'


class AdminAnnouncement(models.Model):
    announcement_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=255)
    body = models.TextField()
    cta_label = models.CharField(max_length=100, blank=True)
    cta_url = models.CharField(max_length=500, blank=True)
    audience_type = models.CharField(
        max_length=32,
        choices=AudienceType.choices,
        default=AudienceType.ALL_USERS,
    )
    starts_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(blank=True, null=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_admin_announcements',
        blank=True,
        null=True,
    )

    class Meta:
        db_table = 'notifications_admin_announcement'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_published', 'starts_at'], name='notif_ann_publish_idx'),
        ]

    def __str__(self):
        return self.title


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
    )
    in_app_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)
    marketing_enabled = models.BooleanField(default=True)
    product_updates_enabled = models.BooleanField(default=True)
    quiet_hours_start = models.TimeField(blank=True, null=True)
    quiet_hours_end = models.TimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notifications_preference'


class Notification(models.Model):
    notification_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        related_name='notifications',
        blank=True,
        null=True,
    )
    announcement = models.ForeignKey(
        AdminAnnouncement,
        on_delete=models.SET_NULL,
        related_name='notifications',
        blank=True,
        null=True,
    )
    notification_type = models.CharField(
        max_length=32,
        choices=NotificationType.LEGACY_CHOICES,
        default=NotificationType.SYSTEM,
    )
    channel = models.CharField(
        max_length=16,
        choices=NotificationChannel.choices,
        default=NotificationChannel.IN_APP,
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    cta_label = models.CharField(max_length=100, blank=True)
    cta_url = models.CharField(max_length=500, blank=True)
    metadata = models.JSONField(blank=True, default=dict)
    status = models.CharField(
        max_length=16,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING,
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notifications_notification'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at'], name='notif_user_unread_idx'),
            models.Index(fields=['notification_type', 'created_at'], name='notif_type_created_idx'),
        ]

    def mark_read(self):
        if self.is_read:
            return
        self.is_read = True
        self.read_at = timezone.now()
        self.status = DeliveryStatus.READ
        self.save(update_fields=['is_read', 'read_at', 'status', 'updated_at'])


class NotificationDelivery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='deliveries',
        null=True,
        blank=True,
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_deliveries')
    channel = models.CharField(
        max_length=20,
        choices=[
            (NotificationChannel.IN_APP, 'In-app'),
            (NotificationChannel.EMAIL, 'Email'),
        ],
    )
    type = models.CharField(max_length=50, choices=NotificationType.DELIVERY_CHOICES)
    template_code = models.CharField(max_length=100, blank=True)
    subject = models.CharField(max_length=255, blank=True)
    rendered_body = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=NotificationStatus.choices, default=NotificationStatus.PENDING)
    error_message = models.TextField(blank=True)
    provider = models.CharField(max_length=100, blank=True)
    provider_message_id = models.CharField(max_length=255, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['channel', 'status', 'created_at'], name='notif_deliv_ch_status_idx'),
            models.Index(fields=['user', 'created_at'], name='notif_deliv_user_created_idx'),
            models.Index(fields=['type', 'created_at'], name='notif_deliv_type_created_idx'),
        ]

    def mark_sent(self, provider: str = '', provider_message_id: str = ''):
        self.status = NotificationStatus.SENT
        self.provider = provider
        self.provider_message_id = provider_message_id
        self.sent_at = timezone.now()
        self.error_message = ''
        self.save(update_fields=['status', 'provider', 'provider_message_id', 'sent_at', 'error_message', 'updated_at'])

    def mark_failed(self, error_message: str):
        self.status = NotificationStatus.FAILED
        self.error_message = error_message[:4000]
        self.save(update_fields=['status', 'error_message', 'updated_at'])
