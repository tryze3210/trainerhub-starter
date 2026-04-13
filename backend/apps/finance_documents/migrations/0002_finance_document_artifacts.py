from django.db import migrations, models
import django.utils.timezone
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("finance_documents", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="financedocument",
            name="artifact_content_type",
            field=models.CharField(max_length=64, blank=True, default="application/pdf"),
        ),
        migrations.AddField(
            model_name="financedocument",
            name="artifact_etag",
            field=models.CharField(max_length=255, blank=True, default=""),
        ),
        migrations.AddField(
            model_name="financedocument",
            name="artifact_generated_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="financedocument",
            name="artifact_size_bytes",
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="financedocument",
            name="artifact_storage_key",
            field=models.CharField(max_length=500, blank=True, default=""),
        ),
        migrations.CreateModel(
            name="FinanceDocumentDelivery",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("document_id", models.UUIDField(db_index=True)),
                ("channel", models.CharField(max_length=32, default="email")),
                ("recipient", models.EmailField(max_length=254)),
                ("status", models.CharField(max_length=32, default="pending")),
                ("attempts", models.PositiveIntegerField(default=0)),
                ("last_error", models.TextField(blank=True, default="")),
                ("provider_message_id", models.CharField(max_length=255, blank=True, default="")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("sent_at", models.DateTimeField(null=True, blank=True)),
            ],
            options={"db_table": "finance_document_deliveries", "ordering": ["-created_at"]},
        ),
    ]
