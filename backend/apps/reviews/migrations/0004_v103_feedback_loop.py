# Generated for TrainerHub v103 review feedback loop.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reviews", "0003_stable_review_index_names"),
    ]

    operations = [
        migrations.AddField(
            model_name="review",
            name="trainer_reply",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="review",
            name="trainer_reply_by_id",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="review",
            name="trainer_replied_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name="review",
            index=models.Index(fields=["trainer_reply_by_id", "trainer_replied_at"], name="reviews_replie_30f28a_idx"),
        ),
    ]
