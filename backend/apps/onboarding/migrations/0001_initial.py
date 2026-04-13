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
            name='OnboardingStepState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('step_code', models.CharField(max_length=64)),
                ('is_completed', models.BooleanField(default=False)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('payload', models.JSONField(default=dict)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='onboarding_steps', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'onboarding_step_state'},
        ),
        migrations.AddConstraint(
            model_name='onboardingstepstate',
            constraint=models.UniqueConstraint(fields=('user', 'step_code'), name='uq_onboarding_user_step_code'),
        ),
    ]
