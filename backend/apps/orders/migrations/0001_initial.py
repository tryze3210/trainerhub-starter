from django.conf import settings
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order_type', models.CharField(max_length=32)),
                ('status', models.CharField(max_length=32, default='pending')),
                ('currency', models.CharField(max_length=8, default='RUB')),
                ('total_amount', models.DecimalField(max_digits=12, decimal_places=2)),
                ('external_checkout_id', models.CharField(max_length=128, blank=True)),
                ('paid_at', models.DateTimeField(null=True, blank=True)),
                ('completed_at', models.DateTimeField(null=True, blank=True)),
                ('user', models.ForeignKey(on_delete=models.PROTECT, related_name='orders', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('item_type', models.CharField(max_length=32)),
                ('item_id', models.UUIDField()),
                ('title_snapshot', models.CharField(max_length=255)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('unit_price', models.DecimalField(max_digits=12, decimal_places=2)),
                ('total_price', models.DecimalField(max_digits=12, decimal_places=2)),
                ('metadata', models.JSONField(default=dict, blank=True)),
                ('order', models.ForeignKey(on_delete=models.CASCADE, related_name='items', to='orders.order')),
            ],
        ),
    ]
