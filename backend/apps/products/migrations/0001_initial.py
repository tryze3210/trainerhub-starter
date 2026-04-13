from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [("trainers", "0001_initial"), ("videos", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("slug", models.SlugField(max_length=160, unique=True)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("product_type", models.CharField(max_length=32)),
                ("access_type", models.CharField(max_length=32)),
                ("status", models.CharField(default="draft", max_length=32)),
                ("currency", models.CharField(default="RUB", max_length=8)),
                ("price_amount", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("trainer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="products", to="trainers.trainerprofile")),
            ],
        ),
        migrations.CreateModel(
            name="ProductItem",
            fields=[
                ("id", models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("position", models.PositiveIntegerField(default=0)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="products.product")),
                ("video", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="videos.video")),
            ],
            options={"ordering": ("position",), "unique_together": {("product", "video")}},
        ),
    ]
