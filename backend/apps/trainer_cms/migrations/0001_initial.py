import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='TrainerVideoDraft',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('trainer_id', models.UUIDField(db_index=True)),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('cover_asset_id', models.UUIDField(blank=True, null=True)),
                ('video_asset_id', models.UUIDField(blank=True, null=True)),
                ('price_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('currency', models.CharField(default='RUB', max_length=3)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('review', 'In review'), ('published', 'Published'), ('archived', 'Archived')], default='draft', max_length=32)),
                ('current_version_number', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='TrainerProgramDraft',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('trainer_id', models.UUIDField(db_index=True)),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('price_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('currency', models.CharField(default='RUB', max_length=3)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('review', 'In review'), ('published', 'Published'), ('archived', 'Archived')], default='draft', max_length=32)),
                ('current_version_number', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='TrainerBundleDraft',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('trainer_id', models.UUIDField(db_index=True)),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('price_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('currency', models.CharField(default='RUB', max_length=3)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('review', 'In review'), ('published', 'Published'), ('archived', 'Archived')], default='draft', max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='ProgramLessonDraft',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('position', models.PositiveIntegerField()),
                ('video_asset_id', models.UUIDField(blank=True, null=True)),
                ('is_preview', models.BooleanField(default=False)),
                ('program_draft', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lessons', to='trainer_cms.trainerprogramdraft')),
            ],
        ),
        migrations.CreateModel(
            name='BundleItemDraft',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('item_type', models.CharField(choices=[('video', 'Video'), ('program', 'Program')], max_length=32)),
                ('target_id', models.UUIDField()),
                ('position', models.PositiveIntegerField()),
                ('bundle_draft', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='trainer_cms.trainerbundledraft')),
            ],
        ),
        migrations.CreateModel(
            name='ContentVersion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('trainer_id', models.UUIDField(db_index=True)),
                ('entity_type', models.CharField(choices=[('video', 'Video'), ('program', 'Program'), ('bundle', 'Bundle')], max_length=32)),
                ('entity_id', models.UUIDField(db_index=True)),
                ('version_number', models.PositiveIntegerField()),
                ('snapshot', models.JSONField()),
                ('published_by_id', models.UUIDField()),
            ],
        ),
    ]
