from django.db import migrations, models


def populate_provider_event_id(apps, schema_editor):
    PaymentWebhookEvent = apps.get_model('payments', 'PaymentWebhookEvent')
    for event in PaymentWebhookEvent.objects.all().iterator():
        event.provider_event_id = f'{event.provider}:{event.external_event_id}'
        event.save(update_fields=['provider_event_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0004_chargeback_dispute_statuses'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymentwebhookevent',
            name='external_event_id',
            field=models.CharField(db_index=True, max_length=160),
        ),
        migrations.AddField(
            model_name='paymentwebhookevent',
            name='provider_event_id',
            field=models.CharField(blank=True, max_length=240, null=True, unique=True),
        ),
        migrations.RunPython(populate_provider_event_id, migrations.RunPython.noop),
    ]
