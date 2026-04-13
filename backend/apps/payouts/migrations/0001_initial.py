from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [("trainers", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="TrainerWallet",
            fields=[
                ("id", models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("currency", models.CharField(default="RUB", max_length=8)),
                ("available_amount", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("pending_amount", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("locked_amount", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("trainer", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="wallet", to="trainers.trainerprofile")),
            ],
        ),
        migrations.CreateModel(
            name="BalanceEntry",
            fields=[
                ("id", models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("entry_type", models.CharField(max_length=32)),
                ("direction", models.CharField(max_length=8)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("currency", models.CharField(default="RUB", max_length=8)),
                ("status", models.CharField(default="pending", max_length=32)),
                ("source_type", models.CharField(max_length=32)),
                ("source_id", models.UUIDField()),
                ("wallet", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="entries", to="payouts.trainerwallet")),
            ],
        ),
        migrations.CreateModel(
            name="PayoutRequest",
            fields=[
                ("id", models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("currency", models.CharField(default="RUB", max_length=8)),
                ("status", models.CharField(default="requested", max_length=32)),
                ("destination_json", models.JSONField(default=dict)),
                ("trainer", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payout_requests", to="trainers.trainerprofile")),
                ("wallet", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="payouts.trainerwallet")),
            ],
        ),
    ]
