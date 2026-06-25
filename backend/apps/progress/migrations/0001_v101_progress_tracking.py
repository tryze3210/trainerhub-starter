import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="VideoProgress",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("video_id", models.CharField(max_length=64)),
                ("watched_seconds", models.PositiveIntegerField(default=0)),
                ("duration_seconds", models.PositiveIntegerField(default=0)),
                ("completion_percent", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("is_completed", models.BooleanField(default=False)),
                ("last_position_seconds", models.PositiveIntegerField(default=0)),
                ("last_watched_at", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="video_progress_records",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "progress_video_progress",
            },
        ),
        migrations.CreateModel(
            name="LessonProgress",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("lesson_id", models.CharField(max_length=64)),
                ("program_id", models.CharField(max_length=64)),
                (
                    "content_type",
                    models.CharField(
                        choices=[("program", "Program"), ("course", "Course")],
                        default="program",
                        max_length=32,
                    ),
                ),
                ("is_completed", models.BooleanField(default=False)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lesson_progress_records",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "progress_lesson_progress",
            },
        ),
        migrations.CreateModel(
            name="ProgramProgress",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("program_id", models.CharField(max_length=64)),
                (
                    "content_type",
                    models.CharField(
                        choices=[("program", "Program"), ("course", "Course")],
                        default="program",
                        max_length=32,
                    ),
                ),
                ("total_lessons", models.PositiveIntegerField(default=0)),
                ("completed_lessons", models.PositiveIntegerField(default=0)),
                ("completion_percent", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("is_completed", models.BooleanField(default=False)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("last_activity_at", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="program_progress_records",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "progress_program_progress",
            },
        ),
        migrations.AddIndex(
            model_name="videoprogress",
            index=models.Index(fields=["user", "video_id"], name="progress_vi_user_id_642528_idx"),
        ),
        migrations.AddIndex(
            model_name="lessonprogress",
            index=models.Index(fields=["user", "content_type", "program_id", "is_completed"], name="progress_le_user_id_977ed3_idx"),
        ),
        migrations.AddIndex(
            model_name="programprogress",
            index=models.Index(fields=["user", "content_type", "program_id"], name="progress_pr_user_id_3df7b9_idx"),
        ),
        migrations.AddConstraint(
            model_name="videoprogress",
            constraint=models.UniqueConstraint(fields=("user", "video_id"), name="uniq_user_video_progress"),
        ),
        migrations.AddConstraint(
            model_name="lessonprogress",
            constraint=models.UniqueConstraint(fields=("user", "lesson_id"), name="uniq_user_lesson_progress"),
        ),
        migrations.AddConstraint(
            model_name="programprogress",
            constraint=models.UniqueConstraint(fields=("user", "program_id"), name="uniq_user_program_progress"),
        ),
    ]
