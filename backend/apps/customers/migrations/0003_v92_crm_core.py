from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('customers', '0002_marketplace_core_v6_10_safe_schema'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomerSegment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=120)),
                ('description', models.TextField(blank=True)),
                ('color', models.CharField(blank=True, max_length=24)),
                ('trainer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='crm_segments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='CustomerNote',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('body', models.TextField()),
                ('visibility', models.CharField(default='trainer_private', max_length=24)),
                ('pinned', models.BooleanField(default=False)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trainer_crm_notes', to=settings.AUTH_USER_MODEL)),
                ('trainer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='crm_customer_notes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-pinned', '-created_at'],
            },
        ),
        migrations.AddField(
            model_name='customersegment',
            name='customers',
            field=models.ManyToManyField(blank=True, related_name='crm_segments', to='customers.customerprofile'),
        ),
        migrations.AddIndex(
            model_name='customernote',
            index=models.Index(fields=['trainer', 'customer', '-created_at'], name='crm_note_trainer_customer_idx'),
        ),
        migrations.AddConstraint(
            model_name='customersegment',
            constraint=models.UniqueConstraint(fields=('trainer', 'name'), name='uniq_crm_segment_per_trainer_name'),
        ),
    ]
