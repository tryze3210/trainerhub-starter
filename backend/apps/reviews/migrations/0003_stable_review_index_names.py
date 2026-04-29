from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('reviews', '0002_trust_quality_fields'),
    ]

    operations = [
        migrations.RenameIndex(
            model_name='review',
            old_name='reviews_rev_target__5e8a7d_idx',
            new_name='reviews_rev_target__c64500_idx',
        ),
        migrations.RenameIndex(
            model_name='review',
            old_name='reviews_rev_author__4eaf5a_idx',
            new_name='reviews_rev_author__7ed6c2_idx',
        ),
        migrations.RenameIndex(
            model_name='review',
            old_name='reviews_rev_trainer_1edc1b_idx',
            new_name='reviews_rev_trainer_1f5706_idx',
        ),
        migrations.RenameIndex(
            model_name='review',
            old_name='reviews_rev_status__ab712a_idx',
            new_name='reviews_rev_status_c24b9b_idx',
        ),
    ]
