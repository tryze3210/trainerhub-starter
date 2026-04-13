from django.conf import settings
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('orders', '0001_initial'),
        ('subscriptions', '0001_initial'),
    ]
    operations = [
        migrations.CreateModel(
            name='Entitlement',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('source_type', models.CharField(max_length=32)),
                ('target_type', models.CharField(max_length=32)),
                ('target_id', models.UUIDField(null=True, blank=True)),
                ('status', models.CharField(max_length=32, default='active')),
                ('starts_at', models.DateTimeField(null=True, blank=True)),
                ('ends_at', models.DateTimeField(null=True, blank=True)),
                ('metadata', models.JSONField(default=dict, blank=True)),
                ('source_order', models.ForeignKey(null=True, blank=True, on_delete=models.PROTECT, related_name='granted_entitlements', to='orders.order')),
                ('source_subscription', models.ForeignKey(null=True, blank=True, on_delete=models.PROTECT, related_name='granted_entitlements', to='subscriptions.subscription')),
                ('user', models.ForeignKey(on_delete=models.PROTECT, related_name='entitlements', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
