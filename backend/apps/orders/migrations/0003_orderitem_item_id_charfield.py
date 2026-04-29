from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0002_marketplace_core_v6_10_safe_schema'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderitem',
            name='item_id',
            field=models.CharField(max_length=64),
        ),
    ]
