from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('entitlements', '0002_marketplace_core_v6_10_safe_schema'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entitlement',
            name='target_id',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
    ]
