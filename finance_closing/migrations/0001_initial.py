from django.db import migrations


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('trainers', '____latest____'),
        ('payouts', '____latest____'),
        ('reconciliation', '____latest____'),
    ]

    operations = [
        # Intentionally left as integration sketch.
        # Generate final migration inside the real repository after wiring app labels.
    ]
