from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("orders", "0001_initial"),
        ("trainers", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AffiliatePartner",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=64, unique=True)),
                ("display_name", models.CharField(max_length=255)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("active", "Active"), ("suspended", "Suspended"), ("archived", "Archived")], default="pending", max_length=32)),
                ("commission_kind", models.CharField(choices=[("percent", "Percent"), ("fixed", "Fixed")], default="percent", max_length=16)),
                ("commission_value", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
                ("attribution_model", models.CharField(choices=[("first_touch", "First touch"), ("last_non_direct", "Last non-direct")], default="last_non_direct", max_length=32)),
                ("cookie_ttl_days", models.PositiveIntegerField(default=30)),
                ("allow_self_referrals", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("trainer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="affiliate_partners", to="trainers.trainerprofile")),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="affiliate_partner", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["display_name"]},
        ),
        migrations.CreateModel(
            name="AffiliateClick",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("landing_path", models.CharField(blank=True, max_length=500)),
                ("referrer_url", models.URLField(blank=True)),
                ("utm_source", models.CharField(blank=True, max_length=128)),
                ("utm_medium", models.CharField(blank=True, max_length=128)),
                ("utm_campaign", models.CharField(blank=True, max_length=128)),
                ("utm_content", models.CharField(blank=True, max_length=128)),
                ("utm_term", models.CharField(blank=True, max_length=128)),
                ("client_key", models.CharField(db_index=True, max_length=128)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True)),
                ("clicked_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("partner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="clicks", to="affiliates.affiliatepartner")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="affiliate_clicks", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-clicked_at"]},
        ),
        migrations.CreateModel(
            name="AffiliateAttribution",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("client_key", models.CharField(db_index=True, max_length=128)),
                ("attributed_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("expires_at", models.DateTimeField()),
                ("is_active", models.BooleanField(default=True)),
                ("snapshot", models.JSONField(blank=True, default=dict)),
                ("click", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="attributions", to="affiliates.affiliateclick")),
                ("partner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="attributions", to="affiliates.affiliatepartner")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="affiliate_attributions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-attributed_at"]},
        ),
        migrations.CreateModel(
            name="OrderAttribution",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("attribution_model", models.CharField(choices=[("first_touch", "First touch"), ("last_non_direct", "Last non-direct")], max_length=32)),
                ("commission_base_amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("commission_amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("currency", models.CharField(default="RUB", max_length=8)),
                ("utm_snapshot", models.JSONField(blank=True, default=dict)),
                ("click_snapshot", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("attributed_user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="attributed_orders", to=settings.AUTH_USER_MODEL)),
                ("click", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="order_attributions", to="affiliates.affiliateclick")),
                ("order", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="affiliate_attribution", to="orders.order")),
                ("partner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="order_attributions", to="affiliates.affiliatepartner")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="AffiliateCommission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("currency", models.CharField(default="RUB", max_length=8)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("reversed", "Reversed"), ("paid", "Paid")], default="pending", max_length=32)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("paid_out_at", models.DateTimeField(blank=True, null=True)),
                ("reversed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="affiliate_commissions", to="orders.order")),
                ("order_attribution", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="commission", to="affiliates.orderattribution")),
                ("partner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="commissions", to="affiliates.affiliatepartner")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
