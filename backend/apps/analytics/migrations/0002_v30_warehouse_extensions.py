from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("analytics", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DailyPlatformFunnel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(unique=True)),
                ("signups", models.PositiveIntegerField(default=0)),
                ("ordering_customers", models.PositiveIntegerField(default=0)),
                ("paid_customers", models.PositiveIntegerField(default=0)),
                ("new_subscribers", models.PositiveIntegerField(default=0)),
                ("signup_to_order_rate", models.DecimalField(decimal_places=4, default=Decimal("0.0000"), max_digits=7)),
                ("order_to_paid_rate", models.DecimalField(decimal_places=4, default=Decimal("0.0000"), max_digits=7)),
                ("paid_to_subscription_rate", models.DecimalField(decimal_places=4, default=Decimal("0.0000"), max_digits=7)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "analytics_daily_platform_funnel",
                "ordering": ["-date"],
            },
        ),
        migrations.CreateModel(
            name="DailyUserCohortRetention",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cohort_date", models.DateField(unique=True)),
                ("cohort_size", models.PositiveIntegerField(default=0)),
                ("retained_day_0", models.PositiveIntegerField(default=0)),
                ("retained_day_1", models.PositiveIntegerField(default=0)),
                ("retained_day_7", models.PositiveIntegerField(default=0)),
                ("retained_day_30", models.PositiveIntegerField(default=0)),
                ("retention_day_1_rate", models.DecimalField(decimal_places=4, default=Decimal("0.0000"), max_digits=7)),
                ("retention_day_7_rate", models.DecimalField(decimal_places=4, default=Decimal("0.0000"), max_digits=7)),
                ("retention_day_30_rate", models.DecimalField(decimal_places=4, default=Decimal("0.0000"), max_digits=7)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "analytics_daily_user_cohort_retention",
                "ordering": ["-cohort_date"],
            },
        ),
        migrations.CreateModel(
            name="AnalyticsRefreshLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("trigger", models.CharField(default="manual", max_length=32)),
                ("range_start", models.DateField()),
                ("range_end", models.DateField()),
                ("status", models.CharField(choices=[("running", "Running"), ("succeeded", "Succeeded"), ("failed", "Failed")], default="running", max_length=16)),
                ("rows_written", models.PositiveIntegerField(default=0)),
                ("error_message", models.TextField(blank=True)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "analytics_refresh_log",
                "ordering": ["-started_at"],
            },
        ),
        migrations.AddIndex(
            model_name="dailyplatformfunnel",
            index=models.Index(fields=["date"], name="analytics_funnel_date_idx"),
        ),
        migrations.AddIndex(
            model_name="dailyusercohortretention",
            index=models.Index(fields=["cohort_date"], name="analytics_cohort_date_idx"),
        ),
        migrations.AddIndex(
            model_name="analyticsrefreshlog",
            index=models.Index(fields=["status", "started_at"], name="analytics_refresh_status_idx"),
        ),
        migrations.AddIndex(
            model_name="analyticsrefreshlog",
            index=models.Index(fields=["range_start", "range_end"], name="analytics_refresh_range_idx"),
        ),
    ]
