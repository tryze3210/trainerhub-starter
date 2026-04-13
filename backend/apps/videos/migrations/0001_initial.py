from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [("users", "0001_initial"), ("trainers", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="MediaAsset",
            fields=[
                ("id", models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("bucket_name", models.CharField(max_length=128)),
                ("object_key", models.CharField(max_length=512, unique=True)),
                ("asset_type", models.CharField(max_length=32)),
                ("visibility", models.CharField(choices=[("private", "Private"), ("public", "Public")], max_length=16)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("uploaded", "Uploaded"), ("verified", "Verified"), ("failed", "Failed"), ("deleted", "Deleted")], default="draft", max_length=32)),
                ("content_type", models.CharField(max_length=128)),
                ("file_size_bytes", models.BigIntegerField(blank=True, null=True)),
                ("original_filename", models.CharField(blank=True, max_length=255)),
                ("checksum_sha256", models.CharField(blank=True, max_length=64)),
                ("metadata_json", models.JSONField(blank=True, default=dict)),
                ("owner_user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="media_assets", to="users.user")),
            ],
        ),
        migrations.CreateModel(
            name="Video",
            fields=[
                ("id", models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("slug", models.SlugField(max_length=160, unique=True)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("duration_seconds", models.IntegerField(blank=True, null=True)),
                ("is_free", models.BooleanField(default=False)),
                ("status", models.CharField(default="draft", max_length=32)),
                ("media_asset", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="video", to="videos.mediaasset")),
                ("trainer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="videos", to="trainers.trainerprofile")),
            ],
        ),
    ]
