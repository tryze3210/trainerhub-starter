# Generated manually for TrainerHub v51: referral reward idempotency hardening.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("referrals", "0001_marketplace_core_v6_10_safe_schema"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="referralreward",
            index=models.Index(fields=["trigger_type", "trigger_reference"], name="ref_reward_trigger_idx"),
        ),
        migrations.AddConstraint(
            model_name="referralreward",
            constraint=models.UniqueConstraint(
                fields=("attribution", "trigger_type", "trigger_reference"),
                name="ref_reward_once_per_trigger",
            ),
        ),
    ]
