import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("trainer_cms", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="programlessondraft",
            name="materials",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.CreateModel(
            name="TrainerCourseDraft",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("trainer_id", models.UUIDField(db_index=True)),
                ("title", models.CharField(max_length=255)),
                ("slug", models.SlugField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("price_amount", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("currency", models.CharField(default="RUB", max_length=3)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("review", "In review"),
                            ("published", "Published"),
                            ("archived", "Archived"),
                        ],
                        default="draft",
                        max_length=32,
                    ),
                ),
                ("current_version_number", models.PositiveIntegerField(default=0)),
                ("metadata", models.JSONField(blank=True, default=dict)),
            ],
        ),
        migrations.CreateModel(
            name="CourseLessonDraft",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("position", models.PositiveIntegerField()),
                ("video_asset_id", models.UUIDField(blank=True, null=True)),
                ("materials", models.JSONField(blank=True, default=list)),
                ("is_preview", models.BooleanField(default=False)),
                (
                    "course_draft",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lessons",
                        to="trainer_cms.trainercoursedraft",
                    ),
                ),
            ],
        ),
        migrations.AlterField(
            model_name="contentversion",
            name="entity_type",
            field=models.CharField(
                choices=[
                    ("video", "Video"),
                    ("course", "Course"),
                    ("program", "Program"),
                    ("bundle", "Bundle"),
                ],
                max_length=32,
            ),
        ),
    ]
