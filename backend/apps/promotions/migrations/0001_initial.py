from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("orders", "0001_initial"),
        ("trainers", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PromoCampaign",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("slug", models.SlugField(unique=True)),
                ("description", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("active", "Active"), ("paused", "Paused"), ("archived", "Archived")], default="draft", max_length=32)),
                ("funding_source", models.CharField(choices=[("platform", "Platform"), ("trainer", "Trainer"), ("shared", "Shared")], max_length=32)),
                ("shared_platform_ratio", models.DecimalField(decimal_places=2, default=Decimal("0.50"), max_digits=5)),
                ("starts_at", models.DateTimeField()),
                ("ends_at", models.DateTimeField(blank=True, null=True)),
                ("max_redemptions_total", models.PositiveIntegerField(blank=True, null=True)),
                ("max_redemptions_per_user", models.PositiveIntegerField(blank=True, null=True)),
                ("is_first_order_only", models.BooleanField(default=False)),
                ("is_new_customer_only", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "trainer",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="promo_campaigns", to="trainers.trainerprofile"),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="PromoCode",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=64, unique=True)),
                ("discount_type", models.CharField(choices=[("fixed", "Fixed"), ("percent", "Percent")], max_length=16)),
                ("discount_value", models.DecimalField(decimal_places=2, max_digits=10)),
                ("min_order_amount", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("max_discount_amount", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "campaign",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="codes", to="promotions.promocampaign"),
                ),
            ],
            options={"ordering": ["code"]},
        ),
        migrations.CreateModel(
            name="PromoRedemption",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("currency", models.CharField(default="RUB", max_length=8)),
                ("subtotal_amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("discount_amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("funded_by_platform_amount", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("funded_by_trainer_amount", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "campaign",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="redemptions", to="promotions.promocampaign"),
                ),
                (
                    "code",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="redemptions", to="promotions.promocode"),
                ),
                (
                    "order",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="promo_redemptions", to="orders.order"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="promo_redemptions", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="promoredemption",
            constraint=models.UniqueConstraint(fields=("code", "order"), name="uq_promo_redemption_code_order"),
        ),
    ]
