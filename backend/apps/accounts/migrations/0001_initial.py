from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('full_name', models.CharField(max_length=255)),
                ('display_name', models.CharField(blank=True, max_length=255)),
                ('phone', models.CharField(blank=True, max_length=32)),
                ('country', models.CharField(blank=True, max_length=2)),
                ('city', models.CharField(blank=True, max_length=255)),
                ('timezone', models.CharField(default='Europe/Berlin', max_length=64)),
                ('preferred_language', models.CharField(default='en', max_length=16)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='account_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'accounts_profile'},
        ),
        migrations.CreateModel(
            name='AccountSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('marketing_emails_enabled', models.BooleanField(default=True)),
                ('product_updates_enabled', models.BooleanField(default=True)),
                ('push_notifications_enabled', models.BooleanField(default=True)),
                ('favorite_categories', models.JSONField(default=list)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='account_settings', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'accounts_settings'},
        ),
        migrations.CreateModel(
            name='AccountRoleAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('role', models.CharField(choices=[('user', 'User'), ('trainer', 'Trainer'), ('admin', 'Admin')], max_length=32)),
                ('is_active', models.BooleanField(default=False)),
                ('granted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='granted_role_assignments', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='role_assignments', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'accounts_role_assignment'},
        ),
        migrations.AddConstraint(
            model_name='accountroleassignment',
            constraint=models.UniqueConstraint(fields=('user', 'role'), name='uq_accounts_role_assignment_user_role'),
        ),
    ]
