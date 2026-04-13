from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = [('orders', '0001_initial')]
    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('provider', models.CharField(max_length=64, default='mock')),
                ('status', models.CharField(max_length=32, default='created')),
                ('amount', models.DecimalField(max_digits=12, decimal_places=2)),
                ('currency', models.CharField(max_length=8, default='RUB')),
                ('external_payment_id', models.CharField(max_length=128, blank=True)),
                ('external_checkout_url', models.URLField(blank=True)),
                ('provider_payload', models.JSONField(default=dict, blank=True)),
                ('confirmed_at', models.DateTimeField(null=True, blank=True)),
                ('order', models.ForeignKey(on_delete=models.PROTECT, related_name='payments', to='orders.order')),
            ],
        ),
        migrations.CreateModel(
            name='PaymentWebhookEvent',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('provider', models.CharField(max_length=64)),
                ('event_type', models.CharField(max_length=64)),
                ('external_event_id', models.CharField(max_length=128, unique=True)),
                ('payload', models.JSONField(default=dict, blank=True)),
                ('processed_at', models.DateTimeField(null=True, blank=True)),
            ],
        ),
    ]
