from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DailyPlatformKPI",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(unique=True)),
                ("total_orders", models.PositiveIntegerField(default=0)),
                ("paid_orders", models.PositiveIntegerField(default=0)),
                ("gross_revenue", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=14)),
                ("paid_revenue", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=14)),
                ("total_new_customers", models.PositiveIntegerField(default=0)),
                ("total_new_trainers", models.PositiveIntegerField(default=0)),
                ("active_subscriptions", models.PositiveIntegerField(default=0)),
                ("new_subscriptions", models.PositiveIntegerField(default=0)),
                ("arppu", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=14)),
                ("conversion_rate", models.DecimalField(decimal_places=4, default=Decimal("0.0000"), max_digits=7)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "analytics_daily_platform_kpi",
                "ordering": ["-date"],
            },
        ),
        migrations.CreateModel(
            name="DailyTrainerKPI",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("trainer_id", models.UUIDField(db_index=True)),
                ("total_orders", models.PositiveIntegerField(default=0)),
                ("paid_orders", models.PositiveIntegerField(default=0)),
                ("gross_revenue", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=14)),
                ("paid_revenue", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=14)),
                ("new_customers", models.PositiveIntegerField(default=0)),
                ("active_subscribers", models.PositiveIntegerField(default=0)),
                ("new_subscriptions", models.PositiveIntegerField(default=0)),
                ("arppu", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=14)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "analytics_daily_trainer_kpi",
                "ordering": ["-date", "trainer_id"],
                "unique_together": {("date", "trainer_id")},
            },
        ),
        migrations.AddIndex(
            model_name="dailyplatformkpi",
            index=models.Index(fields=["date"], name="analytics_plat_date_idx"),
        ),
        migrations.AddIndex(
            model_name="dailytrainerkpi",
            index=models.Index(fields=["date", "trainer_id"], name="analytics_trainer_day_idx"),
        ),
        migrations.AddIndex(
            model_name="dailytrainerkpi",
            index=models.Index(fields=["trainer_id", "date"], name="analytics_trainer_date_idx"),
        ),
    ]
