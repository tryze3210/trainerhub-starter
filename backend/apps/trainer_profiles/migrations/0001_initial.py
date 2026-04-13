import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TrainerPublicProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('trainer_uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('slug', models.SlugField(max_length=255, unique=True)),
                ('display_name', models.CharField(max_length=255)),
                ('headline', models.CharField(blank=True, max_length=255)),
                ('bio', models.TextField(blank=True)),
                ('avatar_url', models.URLField(blank=True)),
                ('specialties', models.JSONField(default=list)),
                ('languages', models.JSONField(default=list)),
                ('is_public', models.BooleanField(default=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='trainer_public_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'trainer_public_profile'},
        ),
    ]
