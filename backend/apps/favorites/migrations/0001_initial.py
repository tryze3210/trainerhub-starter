from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [("customers", "0001_initial"), ("trainers", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="FavoriteTrainer",
            fields=[
                ("id", models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="favorite_trainers", to="customers.customerprofile")),
                ("trainer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="trainers.trainerprofile")),
            ],
            options={"unique_together": {("customer", "trainer")}},
        ),
    ]
