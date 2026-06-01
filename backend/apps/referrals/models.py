import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models


class ReferralProgram(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    reward_kind = models.CharField(max_length=32, default="fixed")
    reward_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    invite_ttl_days = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)


class ReferralCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    program = models.ForeignKey(ReferralProgram, on_delete=models.CASCADE, related_name="codes")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="referral_codes")
    code = models.CharField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)


class ReferralInvite(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONVERTED = "converted"
    STATUS_EXPIRED = "expired"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_CONVERTED, "Converted"),
        (STATUS_EXPIRED, "Expired"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.ForeignKey(ReferralCode, on_delete=models.CASCADE, related_name="invites")
    landing_path = models.CharField(max_length=255, blank=True)
    utm_source = models.CharField(max_length=128, blank=True)
    utm_medium = models.CharField(max_length=128, blank=True)
    utm_campaign = models.CharField(max_length=128, blank=True)
    click_session_key = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING)
    expires_at = models.DateTimeField(null=True, blank=True)
    converted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)


class ReferralAttribution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invite = models.OneToOneField(ReferralInvite, on_delete=models.CASCADE, related_name="attribution")
    referred_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="referral_attributions")
    attribution_model = models.CharField(max_length=32, default="last_click")
    is_locked = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)


class ReferralReward(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attribution = models.ForeignKey(ReferralAttribution, on_delete=models.CASCADE, related_name="rewards")
    trigger_type = models.CharField(max_length=64, default="order_paid")
    trigger_reference = models.CharField(max_length=128, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["trigger_type", "trigger_reference"], name="ref_reward_trigger_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["attribution", "trigger_type", "trigger_reference"],
                name="ref_reward_once_per_trigger",
            ),
        ]


class ReferralLedger(models.Model):
    ENTRY_REWARD = "reward"
    ENTRY_REVERSAL = "reversal"
    ENTRY_CHOICES = [
        (ENTRY_REWARD, "Reward"),
        (ENTRY_REVERSAL, "Reversal"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="referral_ledger_entries")
    reward = models.ForeignKey(ReferralReward, on_delete=models.CASCADE, related_name="ledger_entries", null=True, blank=True)
    entry_type = models.CharField(max_length=32, choices=ENTRY_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
