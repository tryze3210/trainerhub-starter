from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [("customers", "0001_initial"), ("trainers", "0001_initial"), ("products", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="Purchase",
            fields=[
                ("id", models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("status", models.CharField(default="pending", max_length=32)),
                ("gross_amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("platform_commission_amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("trainer_net_amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("currency", models.CharField(default="RUB", max_length=8)),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="purchases", to="customers.customerprofile")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="products.product")),
                ("trainer", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="trainers.trainerprofile")),
            ],
        ),
    ]
