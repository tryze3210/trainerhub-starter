from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("finance_documents", "0002_finance_document_artifacts"),
    ]

    operations = [
        migrations.AlterField(
            model_name="financedocument",
            name="document_type",
            field=models.CharField(
                choices=[
                    ("invoice", "Invoice"),
                    ("receipt", "Receipt"),
                    ("credit_note", "Credit Note"),
                    ("refund_document", "Refund Document"),
                    ("payout_act", "Payout Act"),
                    ("statement", "Statement"),
                ],
                max_length=32,
            ),
        ),
    ]
