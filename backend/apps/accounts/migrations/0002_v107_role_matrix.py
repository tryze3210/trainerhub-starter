# Generated for TrainerHub v107 role matrix / permission audit.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="accountroleassignment",
            name="role",
            field=models.CharField(
                choices=[
                    ("user", "User"),
                    ("trainer", "Trainer"),
                    ("admin", "Admin"),
                    ("support", "Support"),
                    ("finance", "Finance"),
                    ("readonly_auditor", "Readonly auditor"),
                ],
                max_length=32,
            ),
        ),
    ]
