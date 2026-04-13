from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('target_type', models.CharField(max_length=32)),
                ('target_id', models.CharField(max_length=64)),
                ('author_user_id', models.CharField(max_length=64)),
                ('rating', models.PositiveSmallIntegerField()),
                ('title', models.CharField(max_length=160)),
                ('body', models.TextField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('published', 'Published'), ('rejected', 'Rejected')], default='pending', max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
