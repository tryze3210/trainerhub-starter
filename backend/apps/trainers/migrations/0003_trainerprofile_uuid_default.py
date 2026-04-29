# Generated manually for TrainerHub v6.9.
# Safe migration: aligns TrainerProfile model default with the already existing UUID PK column.

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("trainers", "0002_trainer_application"),
    ]

    operations = [
        migrations.AlterField(
            model_name="trainerprofile",
            name="id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
    ]
