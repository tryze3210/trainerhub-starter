from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class AffiliatePartnerStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    ARCHIVED = "archived", "Archived"


class AttributionModel(models.TextChoices):
    FIRST_TOUCH = "first_touch", "First touch"
    LAST_NON_DIRECT = "last_non_direct", "Last non-direct"


class CommissionKind(models.TextChoices):
    PERCENT = "percent", "Percent"
    FIXED = "fixed", "Fixed"


class AffiliatePartner(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="affiliate_partner", on_delete=models.CASCADE)
    code = models.CharField(max_length=64, unique=True)
    display_name = models.CharField(max_length=255)
    status = models.CharField(max_length=32, choices=AffiliatePartnerStatus.choices, default=AffiliatePartnerStatus.PENDING)

    commission_kind = models.CharField(max_length=16, choices=CommissionKind.choices, default=CommissionKind.PERCENT)
    commission_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    attribution_model = models.CharField(
        max_length=32,
        choices=AttributionModel.choices,
        default=AttributionModel.LAST_NON_DIRECT,
    )
    cookie_ttl_days = models.PositiveIntegerField(default=30)

    allow_self_referrals = models.BooleanField(default=False)
    trainer = models.ForeignKey(
        "trainers.TrainerProfile",
        related_name="affiliate_partners",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_name"]

    def clean(self):
        self.code = self.code.strip().upper()
        if self.commission_kind == CommissionKind.PERCENT and self.commission_value > Decimal("100.00"):
            raise ValidationError("Percent commission cannot exceed 100")


class AffiliateClick(models.Model):
    partner = models.ForeignKey(AffiliatePartner, related_name="clicks", on_delete=models.PROTECT)
    landing_path = models.CharField(max_length=500, blank=True)
    referrer_url = models.URLField(blank=True)

    utm_source = models.CharField(max_length=128, blank=True)
    utm_medium = models.CharField(max_length=128, blank=True)
    utm_campaign = models.CharField(max_length=128, blank=True)
    utm_content = models.CharField(max_length=128, blank=True)
    utm_term = models.CharField(max_length=128, blank=True)

    client_key = models.CharField(max_length=128, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="affiliate_clicks", null=True, blank=True, on_delete=models.SET_NULL)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    clicked_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-clicked_at"]


class AffiliateAttribution(models.Model):
    partner = models.ForeignKey(AffiliatePartner, related_name="attributions", on_delete=models.PROTECT)
    click = models.ForeignKey(AffiliateClick, related_name="attributions", null=True, blank=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="affiliate_attributions", null=True, blank=True, on_delete=models.SET_NULL)

    client_key = models.CharField(max_length=128, db_index=True)
    attributed_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-attributed_at"]


class OrderAttribution(models.Model):
    order = models.OneToOneField("orders.Order", related_name="affiliate_attribution", on_delete=models.CASCADE)
    partner = models.ForeignKey(AffiliatePartner, related_name="order_attributions", on_delete=models.PROTECT)
    click = models.ForeignKey(AffiliateClick, related_name="order_attributions", null=True, blank=True, on_delete=models.SET_NULL)

    attributed_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="attributed_orders", null=True, blank=True, on_delete=models.SET_NULL)
    attribution_model = models.CharField(max_length=32, choices=AttributionModel.choices)

    commission_base_amount = models.DecimalField(max_digits=12, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="RUB")

    utm_snapshot = models.JSONField(default=dict, blank=True)
    click_snapshot = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class AffiliateCommissionStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REVERSED = "reversed", "Reversed"
    PAID = "paid", "Paid"


class AffiliateCommission(models.Model):
    order_attribution = models.OneToOneField(OrderAttribution, related_name="commission", on_delete=models.CASCADE)
    partner = models.ForeignKey(AffiliatePartner, related_name="commissions", on_delete=models.PROTECT)
    order = models.ForeignKey("orders.Order", related_name="affiliate_commissions", on_delete=models.PROTECT)

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="RUB")
    status = models.CharField(max_length=32, choices=AffiliateCommissionStatus.choices, default=AffiliateCommissionStatus.PENDING)

    approved_at = models.DateTimeField(null=True, blank=True)
    paid_out_at = models.DateTimeField(null=True, blank=True)
    reversed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
