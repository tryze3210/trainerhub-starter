from django.conf import settings
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ('orders', '0001_initial')]
    operations = [
        migrations.CreateModel(
            name='SubscriptionPlan',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(max_length=64, unique=True)),
                ('title', models.CharField(max_length=255)),
                ('period_days', models.PositiveIntegerField(default=30)),
                ('price', models.DecimalField(max_digits=12, decimal_places=2)),
                ('currency', models.CharField(max_length=8, default='RUB')),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(max_length=32, default='pending')),
                ('starts_at', models.DateTimeField(null=True, blank=True)),
                ('ends_at', models.DateTimeField(null=True, blank=True)),
                ('cancelled_at', models.DateTimeField(null=True, blank=True)),
                ('auto_renew', models.BooleanField(default=False)),
                ('plan', models.ForeignKey(on_delete=models.PROTECT, related_name='subscriptions', to='subscriptions.subscriptionplan')),
                ('source_order', models.ForeignKey(on_delete=models.PROTECT, related_name='created_subscriptions', to='orders.order')),
                ('user', models.ForeignKey(on_delete=models.PROTECT, related_name='subscriptions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
