from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [("users", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="TrainerProfile",
            fields=[
                ("id", models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("slug", models.SlugField(max_length=160, unique=True)),
                ("display_name", models.CharField(max_length=255)),
                ("headline", models.CharField(blank=True, max_length=255)),
                ("bio", models.TextField(blank=True)),
                ("rating_avg", models.DecimalField(decimal_places=2, default=0, max_digits=4)),
                ("views_count", models.BigIntegerField(default=0)),
                ("sales_count", models.BigIntegerField(default=0)),
                ("is_public", models.BooleanField(default=True)),
                ("status", models.CharField(default="pending", max_length=32)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="trainer_profile", to="users.user")),
            ],
        ),
    ]
