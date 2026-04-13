from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="PlatformSettings",
            fields=[
                ("id", models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("default_currency", models.CharField(default="RUB", max_length=8)),
                ("global_commission_rate", models.DecimalField(decimal_places=2, default=20, max_digits=5)),
                ("media_presigned_read_ttl_seconds", models.IntegerField(default=300)),
                ("media_upload_ttl_seconds", models.IntegerField(default=900)),
                ("homepage_config", models.JSONField(blank=True, default=dict)),
            ],
        ),
    ]
