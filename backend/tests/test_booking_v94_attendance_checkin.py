from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.booking.models import BookingAttendance, BookingSlot, SessionReservation


@pytest.mark.django_db
def test_v94_attendance_manual_checkin_checkout_and_external_identifier():
    User = get_user_model()
    trainer = User.objects.create_user(email='attendance-trainer@example.com', password='pass12345', role='trainer')
    customer = User.objects.create_user(email='attendance-customer@example.com', password='pass12345', role='customer')
    slot = BookingSlot.objects.create(
        trainer=trainer,
        starts_at=timezone.now() + timedelta(hours=2),
        ends_at=timezone.now() + timedelta(hours=3),
        capacity=2,
    )

    client = APIClient()
    client.force_authenticate(user=customer)
    reservation_response = client.post(
        '/api/v1/booking/reservations/create/',
        {'slot_id': str(slot.id), 'title': 'Attendance session'},
        format='json',
    )
    assert reservation_response.status_code == 201
    reservation = SessionReservation.objects.get(customer=customer, slot=slot)
    attendance = BookingAttendance.objects.get(reservation=reservation)

    client.force_authenticate(user=trainer)
    checkin_response = client.post(
        '/api/v1/booking/attendance/check-in/',
        {'reservation_id': str(reservation.id), 'method': 'manual', 'external_identifier': 'card-001'},
        format='json',
    )
    assert checkin_response.status_code == 200
    assert checkin_response.json()['status'] == BookingAttendance.STATUS_CHECKED_IN
    assert checkin_response.json()['external_identifier'] == 'card-001'

    checkout_response = client.post(f'/api/v1/booking/attendance/check-out/{attendance.id}/')
    assert checkout_response.status_code == 200
    assert checkout_response.json()['status'] == BookingAttendance.STATUS_ATTENDED

    noshow_response = client.post(
        '/api/v1/booking/attendance/no-show/',
        {'reservation_id': str(reservation.id), 'reason': 'missed'},
        format='json',
    )
    assert noshow_response.status_code == 400

    customer_two = User.objects.create_user(email='attendance-customer-2@example.com', password='pass12345', role='customer')
    client.force_authenticate(user=customer_two)
    second_response = client.post(
        '/api/v1/booking/reservations/create/',
        {'slot_id': str(slot.id), 'title': 'Card check-in session'},
        format='json',
    )
    assert second_response.status_code == 201
    second_reservation = SessionReservation.objects.get(customer=customer_two, slot=slot)
    second_attendance = BookingAttendance.objects.get(reservation=second_reservation)
    second_attendance.external_identifier = 'mifare:abc123'
    second_attendance.save(update_fields=['external_identifier', 'updated_at'])

    client.force_authenticate(user=trainer)
    mifare_response = client.post(
        '/api/v1/booking/attendance/check-in/',
        {'external_identifier': 'mifare:abc123', 'method': 'mifare'},
        format='json',
    )
    assert mifare_response.status_code == 200
    assert mifare_response.json()['checkin_method'] == BookingAttendance.METHOD_MIFARE
