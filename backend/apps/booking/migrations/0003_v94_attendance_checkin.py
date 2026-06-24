from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('booking', '0002_v93_booking_schedule_core'),
    ]

    operations = [
        migrations.CreateModel(
            name='BookingAttendance',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('checkin_token', models.UUIDField(db_index=True, default=uuid.uuid4, unique=True)),
                ('external_identifier', models.CharField(blank=True, db_index=True, max_length=128)),
                ('status', models.CharField(choices=[('expected', 'Expected'), ('checked_in', 'Checked in'), ('attended', 'Attended'), ('no_show', 'No show'), ('cancelled', 'Cancelled')], db_index=True, default='expected', max_length=24)),
                ('checkin_method', models.CharField(choices=[('manual', 'Manual'), ('qr', 'QR'), ('mifare', 'Mifare'), ('external', 'External')], default='manual', max_length=24)),
                ('checked_in_at', models.DateTimeField(blank=True, null=True)),
                ('checked_out_at', models.DateTimeField(blank=True, null=True)),
                ('duration_seconds', models.PositiveIntegerField(default=0)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='booking_attendance_as_customer', to=settings.AUTH_USER_MODEL)),
                ('reservation', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='attendance', to='booking.sessionreservation')),
                ('trainer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='booking_attendance_as_trainer', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddIndex(
            model_name='bookingattendance',
            index=models.Index(fields=['trainer', 'status', 'checked_in_at'], name='booking_att_trainer_status_idx'),
        ),
        migrations.AddIndex(
            model_name='bookingattendance',
            index=models.Index(fields=['customer', 'created_at'], name='booking_att_customer_idx'),
        ),
    ]
