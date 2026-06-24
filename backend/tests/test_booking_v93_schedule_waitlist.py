from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.booking.models import BookingSlot, BookingWaitlistEntry, SessionReservation


@pytest.mark.django_db
def test_v93_booking_capacity_waitlist_and_cancel_promotion():
    User = get_user_model()
    trainer = User.objects.create_user(email='schedule-trainer@example.com', password='pass12345', role='trainer')
    customer_one = User.objects.create_user(email='schedule-c1@example.com', password='pass12345', role='customer')
    customer_two = User.objects.create_user(email='schedule-c2@example.com', password='pass12345', role='customer')
    slot = BookingSlot.objects.create(
        trainer=trainer,
        starts_at=timezone.now() + timedelta(days=1),
        ends_at=timezone.now() + timedelta(days=1, hours=1),
        status=BookingSlot.STATUS_OPEN,
        capacity=1,
    )

    client = APIClient()
    client.force_authenticate(user=customer_one)
    reserve_response = client.post(
        '/api/v1/booking/reservations/create/',
        {'slot_id': str(slot.id), 'title': 'Morning session'},
        format='json',
    )
    assert reserve_response.status_code == 201
    assert SessionReservation.objects.filter(slot=slot, status=SessionReservation.STATUS_CONFIRMED).count() == 1

    client.force_authenticate(user=customer_two)
    full_response = client.post(
        '/api/v1/booking/reservations/create/',
        {'slot_id': str(slot.id), 'title': 'Overflow session'},
        format='json',
    )
    assert full_response.status_code == 400

    waitlist_response = client.post(
        '/api/v1/booking/reservations/waitlist/',
        {'slot_id': str(slot.id), 'title': 'Waitlist me'},
        format='json',
    )
    assert waitlist_response.status_code == 201
    assert BookingWaitlistEntry.objects.filter(slot=slot, customer=customer_two, status=BookingWaitlistEntry.STATUS_WAITING).count() == 1

    first_reservation = SessionReservation.objects.get(slot=slot, customer=customer_one)
    client.force_authenticate(user=trainer)
    cancel_response = client.post(
        f'/api/v1/booking/reservations/{first_reservation.id}/cancel/',
        {'reason': 'trainer_cancelled'},
        format='json',
    )
    assert cancel_response.status_code == 200
    assert SessionReservation.objects.filter(slot=slot, customer=customer_one, status=SessionReservation.STATUS_CANCELLED).count() == 1
    assert SessionReservation.objects.filter(slot=slot, customer=customer_two, status=SessionReservation.STATUS_CONFIRMED).count() == 1
    assert BookingWaitlistEntry.objects.filter(slot=slot, customer=customer_two, status=BookingWaitlistEntry.STATUS_PROMOTED).count() == 1

    schedule_response = client.get('/api/v1/booking/me/schedule/')
    assert schedule_response.status_code == 200
    assert schedule_response.json()['summary']['reservations_confirmed'] == 1
