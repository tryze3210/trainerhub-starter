from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('entitlements', '0003_target_id_charfield'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entitlement',
            name='source_type',
            field=models.CharField(choices=[('order', 'Order'), ('subscription', 'Subscription'), ('admin', 'Admin'), ('admin_grant', 'Admin grant')], max_length=32),
        ),
    ]
