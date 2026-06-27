# Generated for TrainerHub v102 assignments/homework.

import uuid

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
            name="Assignment",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("content_type", models.CharField(choices=[("program", "Program"), ("course", "Course")], max_length=32)),
                ("content_id", models.CharField(db_index=True, max_length=80)),
                ("lesson_id", models.CharField(blank=True, max_length=80)),
                ("due_at", models.DateTimeField(blank=True, null=True)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("published", "Published"), ("archived", "Archived")], default="draft", max_length=32)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("trainer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="trainer_assignments", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "assignments_assignment",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="AssignmentSubmission",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("answer_text", models.TextField(blank=True)),
                ("attachments", models.JSONField(blank=True, default=list)),
                ("status", models.CharField(choices=[("submitted", "Submitted"), ("reviewed", "Reviewed"), ("needs_revision", "Needs revision"), ("approved", "Approved")], default="submitted", max_length=32)),
                ("submitted_at", models.DateTimeField()),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("review_comment", models.TextField(blank=True)),
                ("score", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ("assignment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="submissions", to="assignments.assignment")),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_assignment_submissions", to=settings.AUTH_USER_MODEL)),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assignment_submissions", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "assignments_submission",
                "ordering": ["-submitted_at", "-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="assignment",
            index=models.Index(fields=["content_type", "content_id", "status"], name="assignments_target_status_idx"),
        ),
        migrations.AddIndex(
            model_name="assignment",
            index=models.Index(fields=["trainer", "status"], name="assignments_trainer_status_idx"),
        ),
        migrations.AddIndex(
            model_name="assignmentsubmission",
            index=models.Index(fields=["student", "status"], name="asg_sub_stu_stat_idx"),
        ),
        migrations.AddIndex(
            model_name="assignmentsubmission",
            index=models.Index(fields=["assignment", "status"], name="asg_sub_asg_stat_idx"),
        ),
        migrations.AddConstraint(
            model_name="assignmentsubmission",
            constraint=models.UniqueConstraint(fields=("assignment", "student"), name="uq_asg_sub_student"),
        ),
    ]
