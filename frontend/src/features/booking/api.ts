export async function fetchTrainerBookingCalendar() {
  const res = await fetch('/api/v1/booking/me/calendar/', { credentials: 'include' });
  if (!res.ok) throw new Error('Failed to load booking calendar');
  return res.json();
}

export async function fetchMyReservations() {
  const res = await fetch('/api/v1/booking/me/reservations/', { credentials: 'include' });
  if (!res.ok) throw new Error('Failed to load reservations');
  return res.json();
}

export async function fetchAdminBookingOverview() {
  const res = await fetch('/api/v1/booking/admin/overview/', { credentials: 'include' });
  if (!res.ok) throw new Error('Failed to load booking overview');
  return res.json();
}
