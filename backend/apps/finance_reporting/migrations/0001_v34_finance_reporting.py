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
            name="SettlementReport",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("period_start", models.DateField()),
                ("period_end", models.DateField()),
                ("status", models.CharField(max_length=32, default="draft", choices=[("draft", "Draft"), ("finalized", "Finalized"), ("exported", "Exported")])),
                ("generated_at", models.DateTimeField(auto_now_add=True)),
                ("finalized_at", models.DateTimeField(null=True, blank=True)),
                ("export_count", models.PositiveIntegerField(default=0)),
                ("currency", models.CharField(max_length=8, default="RUB")),
                ("notes", models.TextField(blank=True, default="")),
            ],
            options={"db_table": "finance_settlement_reports", "ordering": ("-period_end", "-generated_at")},
        ),
        migrations.CreateModel(
            name="FinanceReconciliationSnapshot",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("snapshot_date", models.DateField(unique=True)),
                ("gross_sales_amount", models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ("successful_payment_amount", models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ("refunded_amount", models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ("trainer_payout_amount", models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ("recognized_commission_amount", models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ("settlement_gap_amount", models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ("unmatched_payment_count", models.PositiveIntegerField(default=0)),
                ("unmatched_payout_count", models.PositiveIntegerField(default=0)),
                ("refreshed_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "finance_reconciliation_snapshots", "ordering": ("-snapshot_date",)},
        ),
        migrations.CreateModel(
            name="TrainerSettlementLine",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("gross_amount", models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ("refund_amount", models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ("commission_amount", models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ("payout_amount", models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ("paid_amount", models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ("pending_amount", models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ("order_count", models.PositiveIntegerField(default=0)),
                ("refund_count", models.PositiveIntegerField(default=0)),
                ("payout_count", models.PositiveIntegerField(default=0)),
                ("last_order_at", models.DateTimeField(null=True, blank=True)),
                ("report", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lines", to="finance_reporting.settlementreport")),
                ("trainer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="settlement_lines", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "finance_trainer_settlement_lines", "ordering": ("-payout_amount",), "unique_together": {("report", "trainer")}},
        ),
    ]
