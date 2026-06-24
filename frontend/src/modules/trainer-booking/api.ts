import { apiRequest } from '@/lib/api-client';

export type BookingProfile = {
  id: string;
  timezone: string;
  session_buffer_minutes: number;
  min_notice_hours: number;
  max_future_days: number;
  is_active: boolean;
};

export type AvailabilityRule = {
  id: string;
  weekday: number;
  start_minute: number;
  end_minute: number;
  slot_size_minutes: number;
  is_active: boolean;
};

export type BookingSlot = {
  id: string;
  trainer: string;
  starts_at: string;
  ends_at: string;
  status: string;
  capacity: number;
  source: string;
  reservations_count: number;
  waitlist_count: number;
};

export type SessionReservation = {
  id: string;
  status: string;
  title: string;
  notes: string;
  customer_email?: string;
  customer_name?: string;
  attendance?: BookingAttendance | null;
  slot: BookingSlot;
  created_at: string;
};

export type BookingWaitlistEntry = {
  id: string;
  status: string;
  title: string;
  notes: string;
  customer_email?: string;
  customer_name?: string;
  slot: BookingSlot;
  created_at: string;
};

export type BookingAttendance = {
  id: string;
  reservation_id: string;
  customer_email?: string;
  customer_name?: string;
  checkin_token: string;
  external_identifier: string;
  status: string;
  checkin_method: string;
  checked_in_at?: string | null;
  checked_out_at?: string | null;
  duration_seconds: number;
  slot_starts_at?: string | null;
  slot_ends_at?: string | null;
};

export type TrainerBookingSchedule = {
  profile: BookingProfile;
  slots: BookingSlot[];
  reservations: SessionReservation[];
  attendance: BookingAttendance[];
  waitlist: BookingWaitlistEntry[];
  summary: {
    slots_total: number;
    slots_open: number;
    reservations_confirmed: number;
    attendance_checked_in: number;
    attendance_no_show: number;
    waitlist_waiting: number;
  };
};

export const trainerBookingApi = {
  getSchedule(days = 30) {
    return apiRequest<TrainerBookingSchedule>(`/booking/me/schedule/?days=${days}`, { auth: true });
  },
  getRules() {
    return apiRequest<AvailabilityRule[]>('/booking/me/availability-rules/', { auth: true });
  },
  createRule(payload: Omit<AvailabilityRule, 'id'>) {
    return apiRequest<AvailabilityRule>('/booking/me/availability-rules/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  generateSlots(startDate: string, endDate: string) {
    return apiRequest<{ created: number; existing: number }>('/booking/me/generate-slots/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify({ start_date: startDate, end_date: endDate }),
    });
  },
  cancelReservation(reservationId: string, reason = '') {
    return apiRequest<SessionReservation>(`/booking/reservations/${reservationId}/cancel/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  },
  checkIn(reservationId: string, method: 'manual' | 'qr' | 'mifare' | 'external' = 'manual', externalIdentifier = '') {
    return apiRequest<BookingAttendance>('/booking/attendance/check-in/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify({ reservation_id: reservationId, method, external_identifier: externalIdentifier }),
    });
  },
  checkOut(attendanceId: string) {
    return apiRequest<BookingAttendance>(`/booking/attendance/check-out/${attendanceId}/`, {
      auth: true,
      method: 'POST',
    });
  },
  markNoShow(reservationId: string, reason = '') {
    return apiRequest<BookingAttendance>('/booking/attendance/no-show/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify({ reservation_id: reservationId, reason }),
    });
  },
};
