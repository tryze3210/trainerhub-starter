from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0003_legacy_plan_fields_nullable_source_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='status',
            field=models.CharField(
                choices=[
                    ('trial', 'Trial'),
                    ('pending', 'Pending'),
                    ('active', 'Active'),
                    ('past_due', 'Past due'),
                    ('cancelled', 'Cancelled'),
                    ('expired', 'Expired'),
                ],
                default='pending',
                max_length=32,
            ),
        ),
    ]
