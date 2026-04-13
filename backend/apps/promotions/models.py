from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class PromoCampaignStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    ARCHIVED = "archived", "Archived"


class DiscountType(models.TextChoices):
    FIXED = "fixed", "Fixed"
    PERCENT = "percent", "Percent"


class DiscountFundingSource(models.TextChoices):
    PLATFORM = "platform", "Platform"
    TRAINER = "trainer", "Trainer"
    SHARED = "shared", "Shared"


class PromoCampaign(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=32, choices=PromoCampaignStatus.choices, default=PromoCampaignStatus.DRAFT)

    funding_source = models.CharField(max_length=32, choices=DiscountFundingSource.choices)
    shared_platform_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.50"))

    trainer = models.ForeignKey(
        "trainers.TrainerProfile",
        related_name="promo_campaigns",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)

    max_redemptions_total = models.PositiveIntegerField(null=True, blank=True)
    max_redemptions_per_user = models.PositiveIntegerField(null=True, blank=True)

    is_first_order_only = models.BooleanField(default=False)
    is_new_customer_only = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.funding_source == DiscountFundingSource.SHARED:
            if self.shared_platform_ratio < Decimal("0.00") or self.shared_platform_ratio > Decimal("1.00"):
                raise ValidationError("shared_platform_ratio must be between 0.00 and 1.00")

        if self.ends_at and self.ends_at <= self.starts_at:
            raise ValidationError("ends_at must be after starts_at")

    @property
    def is_active_now(self) -> bool:
        now = timezone.now()
        if self.status != PromoCampaignStatus.ACTIVE:
            return False
        if self.starts_at > now:
            return False
        if self.ends_at and self.ends_at <= now:
            return False
        return True


class PromoCode(models.Model):
    campaign = models.ForeignKey(PromoCampaign, related_name="codes", on_delete=models.CASCADE)
    code = models.CharField(max_length=64, unique=True)
    discount_type = models.CharField(max_length=16, choices=DiscountType.choices)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]

    def clean(self):
        normalized = self.code.strip().upper()
        self.code = normalized
        if self.discount_type == DiscountType.PERCENT and self.discount_value > Decimal("100.00"):
            raise ValidationError("Percent discount cannot exceed 100")


class PromoRedemption(models.Model):
    campaign = models.ForeignKey(PromoCampaign, related_name="redemptions", on_delete=models.PROTECT)
    code = models.ForeignKey(PromoCode, related_name="redemptions", on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="promo_redemptions", on_delete=models.PROTECT)
    order = models.ForeignKey("orders.Order", related_name="promo_redemptions", on_delete=models.PROTECT)

    currency = models.CharField(max_length=8, default="RUB")
    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2)
    funded_by_platform_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    funded_by_trainer_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["code", "order"], name="uq_promo_redemption_code_order"),
        ]
