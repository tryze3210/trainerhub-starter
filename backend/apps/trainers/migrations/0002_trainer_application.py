import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('trainers', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TrainerApplication',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('submitted', 'Submitted'), ('under_review', 'Under review'), ('approved', 'Approved'), ('changes_requested', 'Changes requested'), ('rejected', 'Rejected')], default='draft', max_length=32)),
                ('legal_name', models.CharField(blank=True, max_length=255)),
                ('brand_name', models.CharField(blank=True, max_length=255)),
                ('contact_phone', models.CharField(blank=True, max_length=32)),
                ('country', models.CharField(blank=True, max_length=2)),
                ('city', models.CharField(blank=True, max_length=255)),
                ('specialties', models.JSONField(blank=True, default=list)),
                ('links', models.JSONField(blank=True, default=list)),
                ('bio', models.TextField(blank=True)),
                ('experience_years', models.PositiveSmallIntegerField(default=0)),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('reviewer_note', models.TextField(blank=True)),
                ('latest_moderation_case_id', models.UUIDField(blank=True, null=True)),
                ('moderation_snapshot', models.JSONField(blank=True, default=dict)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='trainer_application', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'trainers_application'},
        ),
    ]
