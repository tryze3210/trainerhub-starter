import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('reviews', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='entitlement_id',
            field=models.CharField(blank=True, default='', max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='review',
            name='moderated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='review',
            name='moderated_by_id',
            field=models.CharField(blank=True, default='', max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='review',
            name='moderation_note',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='review',
            name='quality_flags',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='review',
            name='target_slug',
            field=models.CharField(blank=True, default='', max_length=160),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='review',
            name='target_title',
            field=models.CharField(blank=True, default='', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='review',
            name='trainer_id',
            field=models.CharField(blank=True, default='', max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='review',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='review',
            name='verified_purchase',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='review',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('published', 'Published'), ('rejected', 'Rejected'), ('flagged', 'Flagged')], default='pending', max_length=16),
        ),
        migrations.AddIndex(
            model_name='review',
            index=models.Index(fields=['target_type', 'target_id', 'status'], name='reviews_rev_target__5e8a7d_idx'),
        ),
        migrations.AddIndex(
            model_name='review',
            index=models.Index(fields=['author_user_id', 'target_type', 'target_id'], name='reviews_rev_author__4eaf5a_idx'),
        ),
        migrations.AddIndex(
            model_name='review',
            index=models.Index(fields=['trainer_id', 'status'], name='reviews_rev_trainer_1edc1b_idx'),
        ),
        migrations.AddIndex(
            model_name='review',
            index=models.Index(fields=['status', 'created_at'], name='reviews_rev_status__ab712a_idx'),
        ),
        migrations.AlterModelOptions(
            name='review',
            options={'ordering': ['-created_at']},
        ),
    ]
