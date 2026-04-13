from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TrainerFinanceProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("legal_name", models.CharField(blank=True, max_length=255)),
                ("tax_number", models.CharField(blank=True, max_length=64)),
                ("bank_name", models.CharField(blank=True, max_length=255)),
                ("bank_account", models.CharField(blank=True, max_length=128)),
                ("bank_bic", models.CharField(blank=True, max_length=64)),
                ("payout_currency", models.CharField(default="RUB", max_length=16)),
                ("is_verified", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("trainer", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="finance_profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "trainer_finance_profiles"},
        ),
        migrations.CreateModel(
            name="FinanceDocument",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("document_type", models.CharField(choices=[("invoice", "Invoice"), ("payout_act", "Payout Act"), ("statement", "Statement")], max_length=32)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("finalized", "Finalized")], default="draft", max_length=32)),
                ("period_start", models.DateField()),
                ("period_end", models.DateField()),
                ("document_number", models.CharField(max_length=64)),
                ("currency", models.CharField(default="RUB", max_length=16)),
                ("gross_amount", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("commission_amount", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("net_amount", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("rendered_html", models.TextField(blank=True)),
                ("artifact_path", models.CharField(blank=True, max_length=512)),
                ("finalized_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("trainer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="finance_documents", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "finance_documents", "ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="financedocument",
            index=models.Index(fields=["trainer", "document_type", "period_start", "period_end"], name="finance_doc_trainer_period_idx"),
        ),
        migrations.AddIndex(
            model_name="financedocument",
            index=models.Index(fields=["status", "created_at"], name="finance_doc_status_created_idx"),
        ),
    ]
