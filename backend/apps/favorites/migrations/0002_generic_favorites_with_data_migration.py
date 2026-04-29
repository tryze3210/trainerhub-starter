# Generated manually for marketplace core v6.10.
# Safe migration: copies existing FavoriteTrainer rows into the new generic Favorite table
# before removing the legacy table from the schema state.

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


def copy_trainer_favorites_forward(apps, schema_editor):
    FavoriteTrainer = apps.get_model('favorites', 'FavoriteTrainer')
    Favorite = apps.get_model('favorites', 'Favorite')

    qs = FavoriteTrainer.objects.select_related('customer', 'trainer').all()
    for legacy in qs.iterator():
        user_id = getattr(legacy.customer, 'user_id', None)
        trainer_id = getattr(legacy, 'trainer_id', None)
        if not user_id or not trainer_id:
            continue
        Favorite.objects.get_or_create(
            user_id=user_id,
            target_type='trainer',
            target_id=str(trainer_id),
            defaults={},
        )


def copy_trainer_favorites_backward(apps, schema_editor):
    FavoriteTrainer = apps.get_model('favorites', 'FavoriteTrainer')
    Favorite = apps.get_model('favorites', 'Favorite')
    CustomerProfile = apps.get_model('customers', 'CustomerProfile')
    TrainerProfile = apps.get_model('trainers', 'TrainerProfile')

    qs = Favorite.objects.filter(target_type='trainer')
    for favorite in qs.iterator():
        try:
            customer = CustomerProfile.objects.get(user_id=favorite.user_id)
            trainer = TrainerProfile.objects.get(id=favorite.target_id)
        except Exception:
            continue
        FavoriteTrainer.objects.get_or_create(customer=customer, trainer=trainer)


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('favorites', '0001_initial'),
        ('customers', '0001_initial'),
        ('trainers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Favorite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('target_type', models.CharField(choices=[('trainer', 'Trainer'), ('video', 'Video'), ('program', 'Program')], max_length=32)),
                ('target_id', models.CharField(max_length=64)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorites', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'favorites_favorite',
                'indexes': [models.Index(fields=['user', 'target_type'], name='favorites_f_user_id_ec7f89_idx')],
                'constraints': [models.UniqueConstraint(fields=('user', 'target_type', 'target_id'), name='uniq_user_favorite')],
            },
        ),
        migrations.RunPython(copy_trainer_favorites_forward, copy_trainer_favorites_backward),
        migrations.DeleteModel(name='FavoriteTrainer'),
    ]
