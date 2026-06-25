from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("entitlements", "0004_add_admin_grant_choice"),
    ]

    operations = [
        migrations.AlterField(
            model_name="entitlement",
            name="target_type",
            field=models.CharField(
                choices=[
                    ("video", "Video"),
                    ("course", "Course"),
                    ("program", "Program"),
                    ("bundle", "Bundle"),
                    ("library", "Library"),
                ],
                max_length=32,
            ),
        ),
    ]
