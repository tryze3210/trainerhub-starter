from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('booking', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BookingProfile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('timezone', models.CharField(default='Europe/Berlin', max_length=64)),
                ('session_buffer_minutes', models.PositiveIntegerField(default=15)),
                ('min_notice_hours', models.PositiveIntegerField(default=12)),
                ('max_future_days', models.PositiveIntegerField(default=45)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('trainer', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='booking_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='AvailabilityRule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('weekday', models.PositiveSmallIntegerField()),
                ('start_minute', models.PositiveIntegerField()),
                ('end_minute', models.PositiveIntegerField()),
                ('slot_size_minutes', models.PositiveIntegerField(default=60)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('trainer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='availability_rules', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='AvailabilityException',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date', models.DateField()),
                ('is_blocked', models.BooleanField(default=True)),
                ('start_minute', models.PositiveIntegerField(blank=True, null=True)),
                ('end_minute', models.PositiveIntegerField(blank=True, null=True)),
                ('note', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('trainer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='availability_exceptions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='BookingSlot',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('starts_at', models.DateTimeField(db_index=True)),
                ('ends_at', models.DateTimeField()),
                ('status', models.CharField(choices=[('open', 'Open'), ('held', 'Held'), ('reserved', 'Reserved'), ('cancelled', 'Cancelled')], db_index=True, default='open', max_length=16)),
                ('capacity', models.PositiveIntegerField(default=1)),
                ('source', models.CharField(default='generated', max_length=32)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('trainer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='booking_slots', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SessionReservation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled'), ('completed', 'Completed')], db_index=True, default='pending', max_length=16)),
                ('title', models.CharField(max_length=255)),
                ('notes', models.TextField(blank=True)),
                ('external_ref', models.CharField(blank=True, max_length=128)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='session_reservations_as_customer', to=settings.AUTH_USER_MODEL)),
                ('slot', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reservations', to='booking.bookingslot')),
                ('trainer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='session_reservations_as_trainer', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='BookingEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('event_type', models.CharField(max_length=64)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('reservation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='booking.sessionreservation')),
            ],
        ),
        migrations.CreateModel(
            name='BookingWaitlistEntry',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('waiting', 'Waiting'), ('promoted', 'Promoted'), ('cancelled', 'Cancelled')], db_index=True, default='waiting', max_length=16)),
                ('title', models.CharField(blank=True, max_length=255)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='booking_waitlist_as_customer', to=settings.AUTH_USER_MODEL)),
                ('promoted_reservation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='waitlist_source', to='booking.sessionreservation')),
                ('slot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='waitlist_entries', to='booking.bookingslot')),
                ('trainer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='booking_waitlist_as_trainer', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddIndex(
            model_name='bookingslot',
            index=models.Index(fields=['trainer', 'starts_at', 'status'], name='booking_boo_trainer_f096eb_idx'),
        ),
        migrations.AddIndex(
            model_name='bookingwaitlistentry',
            index=models.Index(fields=['slot', 'status', 'created_at'], name='booking_wai_slot_id_e2fa8d_idx'),
        ),
        migrations.AddConstraint(
            model_name='bookingslot',
            constraint=models.UniqueConstraint(fields=('trainer', 'starts_at'), name='uniq_booking_slot_per_trainer_start'),
        ),
        migrations.AddConstraint(
            model_name='bookingwaitlistentry',
            constraint=models.UniqueConstraint(fields=('slot', 'customer', 'status'), name='uniq_waiting_customer_per_slot'),
        ),
    ]
