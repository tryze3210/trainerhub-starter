from django.db import migrations, models


def backfill_plan_codes(apps, schema_editor):
    SubscriptionPlan = apps.get_model('subscriptions', 'SubscriptionPlan')
    for plan in SubscriptionPlan.objects.filter(code=''):
        plan.code = f'plan-{str(plan.id)[:8]}'
        plan.save(update_fields=['code'])


class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0003_orderitem_item_id_charfield'),
        ('subscriptions', '0002_marketplace_core_v6_10_safe_schema'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscriptionplan',
            name='code',
            field=models.CharField(blank=True, max_length=64, unique=True),
        ),
        migrations.AddField(
            model_name='subscriptionplan',
            name='trainer_id',
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
        migrations.AddField(
            model_name='subscriptionplan',
            name='billing_period',
            field=models.CharField(choices=[('month', 'Month'), ('year', 'Year')], default='month', max_length=16),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='source_order',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.PROTECT, related_name='created_subscriptions', to='orders.order'),
        ),
        migrations.RunPython(backfill_plan_codes, migrations.RunPython.noop),
    ]
