# Generated manually for TrainerHub v6.9.
# Keeps the existing payouts.0001 schema and only adds application-level UUID defaults.

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payouts", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="trainerwallet",
            name="id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="balanceentry",
            name="id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="payoutrequest",
            name="id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
    ]
