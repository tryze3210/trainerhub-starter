'use client';

import { useEffect, useMemo, useState } from 'react';
import { trainerBookingApi, type AvailabilityRule, type TrainerBookingSchedule } from '@/modules/trainer-booking/api';

const DAY_OPTIONS = [14, 30, 60, 90];
const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

function dateTime(value?: string | null) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function toDateInput(date: Date) {
  return date.toISOString().slice(0, 10);
}

function minuteLabel(value: number) {
  const hours = Math.floor(value / 60).toString().padStart(2, '0');
  const minutes = (value % 60).toString().padStart(2, '0');
  return `${hours}:${minutes}`;
}

function parseTime(value: string) {
  const [hours, minutes] = value.split(':').map((part) => Number(part));
  return (Number.isFinite(hours) ? hours : 0) * 60 + (Number.isFinite(minutes) ? minutes : 0);
}

function StatCard({ title, value, hint }: { title: string; value: string | number; hint?: string }) {
  return (
    <div className="card">
      <div className="kpi">
        <span className="muted">{title}</span>
        <strong>{value}</strong>
        {hint ? <small className="muted">{hint}</small> : null}
      </div>
    </div>
  );
}

function RuleList({ rules }: { rules: AvailabilityRule[] }) {
  if (!rules.length) return <p className="muted">Правила доступности пока не настроены.</p>;
  return (
    <div className="stack" style={{ gap: 10 }}>
      {rules.map((rule) => (
        <div key={rule.id} className="list-item">
          <strong>{WEEKDAYS[rule.weekday] || rule.weekday}</strong>
          <span className="muted">
            {minuteLabel(rule.start_minute)}-{minuteLabel(rule.end_minute)} · {rule.slot_size_minutes} min · {rule.is_active ? 'active' : 'paused'}
          </span>
        </div>
      ))}
    </div>
  );
}

export function TrainerBookingDashboard() {
  const [days, setDays] = useState(30);
  const [state, setState] = useState<TrainerBookingSchedule | null>(null);
  const [rules, setRules] = useState<AvailabilityRule[]>([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [weekday, setWeekday] = useState(0);
  const [startTime, setStartTime] = useState('09:00');
  const [endTime, setEndTime] = useState('18:00');
  const [slotSize, setSlotSize] = useState(60);
  const [rangeStart, setRangeStart] = useState(toDateInput(new Date()));
  const [rangeEnd, setRangeEnd] = useState(toDateInput(new Date(Date.now() + 14 * 24 * 60 * 60 * 1000)));

  async function load(selectedDays = days) {
    try {
      setLoading(true);
      setMessage('');
      const [schedule, ruleRows] = await Promise.all([
        trainerBookingApi.getSchedule(selectedDays),
        trainerBookingApi.getRules(),
      ]);
      setState(schedule);
      setRules(ruleRows);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Не удалось загрузить расписание');
    } finally {
      setLoading(false);
    }
  }

  async function createRule() {
    try {
      setSaving(true);
      await trainerBookingApi.createRule({
        weekday,
        start_minute: parseTime(startTime),
        end_minute: parseTime(endTime),
        slot_size_minutes: slotSize,
        is_active: true,
      });
      await load(days);
    } finally {
      setSaving(false);
    }
  }

  async function generateSlots() {
    try {
      setSaving(true);
      const result = await trainerBookingApi.generateSlots(rangeStart, rangeEnd);
      setMessage(`Slots generated: ${result.created} created, ${result.existing} already existed.`);
      await load(days);
    } finally {
      setSaving(false);
    }
  }

  async function cancelReservation(reservationId: string) {
    try {
      setSaving(true);
      await trainerBookingApi.cancelReservation(reservationId, 'trainer_schedule_cancel');
      await load(days);
    } finally {
      setSaving(false);
    }
  }

  async function checkIn(reservationId: string) {
    try {
      setSaving(true);
      await trainerBookingApi.checkIn(reservationId, 'manual');
      await load(days);
    } finally {
      setSaving(false);
    }
  }

  async function checkOut(attendanceId: string) {
    try {
      setSaving(true);
      await trainerBookingApi.checkOut(attendanceId);
      await load(days);
    } finally {
      setSaving(false);
    }
  }

  async function markNoShow(reservationId: string) {
    try {
      setSaving(true);
      await trainerBookingApi.markNoShow(reservationId, 'trainer_schedule_no_show');
      await load(days);
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => {
    void load(days);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days]);

  const upcomingSlots = useMemo(() => state?.slots.slice(0, 80) || [], [state?.slots]);

  return (
    <section className="stack" style={{ gap: 24 }}>
      <div className="card row" style={{ gap: 16, alignItems: 'flex-end' }}>
        <div className="stack" style={{ gap: 8 }}>
          <span className="badge secondary">Booking / Schedule</span>
          <h2 className="title-md">Расписание тренера</h2>
          <p className="muted">Доступность, генерация слотов, лимиты мест, отмены и waitlist.</p>
        </div>
        <div className="inline" style={{ gap: 10, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
          <select className="input" value={days} onChange={(event) => setDays(Number(event.target.value))}>
            {DAY_OPTIONS.map((option) => <option key={option} value={option}>{option} дней</option>)}
          </select>
          <button type="button" className="button secondary" onClick={() => void load()} disabled={loading}>
            Refresh
          </button>
        </div>
      </div>

      {message ? <div className="card">{message}</div> : null}
      {loading && !state ? <div className="card">Загрузка расписания...</div> : null}

      {state ? (
        <>
          <div className="grid-4">
            <StatCard title="Slots" value={state.summary.slots_total} />
            <StatCard title="Open" value={state.summary.slots_open} />
            <StatCard title="Reservations" value={state.summary.reservations_confirmed} />
            <StatCard title="Checked in" value={state.summary.attendance_checked_in} />
            <StatCard title="No-show" value={state.summary.attendance_no_show} />
          </div>

          <div className="grid-2">
            <div className="card">
              <h3 className="title-md">Availability rules</h3>
              <div className="grid-4" style={{ marginBottom: 16 }}>
                <select className="input" value={weekday} onChange={(event) => setWeekday(Number(event.target.value))}>
                  {WEEKDAYS.map((label, index) => <option key={label} value={index}>{label}</option>)}
                </select>
                <input className="input" type="time" value={startTime} onChange={(event) => setStartTime(event.target.value)} />
                <input className="input" type="time" value={endTime} onChange={(event) => setEndTime(event.target.value)} />
                <input className="input" type="number" min={15} max={240} step={15} value={slotSize} onChange={(event) => setSlotSize(Number(event.target.value))} />
              </div>
              <button type="button" className="button secondary" onClick={() => void createRule()} disabled={saving}>
                Add rule
              </button>
              <div style={{ marginTop: 18 }}>
                <RuleList rules={rules} />
              </div>
            </div>

            <div className="card">
              <h3 className="title-md">Generate slots</h3>
              <div className="grid-2" style={{ marginBottom: 16 }}>
                <input className="input" type="date" value={rangeStart} onChange={(event) => setRangeStart(event.target.value)} />
                <input className="input" type="date" value={rangeEnd} onChange={(event) => setRangeEnd(event.target.value)} />
              </div>
              <button type="button" className="button secondary" onClick={() => void generateSlots()} disabled={saving}>
                Generate
              </button>
              <p className="muted" style={{ marginTop: 12 }}>Profile timezone: {state.profile.timezone}</p>
            </div>
          </div>

          <div className="card">
            <h3 className="title-md">Slots</h3>
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Start</th>
                    <th>Status</th>
                    <th>Capacity</th>
                    <th>Waitlist</th>
                    <th>Source</th>
                  </tr>
                </thead>
                <tbody>
                  {upcomingSlots.map((slot) => (
                    <tr key={slot.id}>
                      <td>{dateTime(slot.starts_at)}</td>
                      <td><span className="badge secondary">{slot.status}</span></td>
                      <td>{slot.reservations_count}/{slot.capacity}</td>
                      <td>{slot.waitlist_count}</td>
                      <td>{slot.source}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="grid-2">
            <div className="card">
              <h3 className="title-md">Reservations</h3>
              <div className="stack" style={{ gap: 10 }}>
                {state.reservations.map((reservation) => (
                  <div key={reservation.id} className="list-item">
                    <strong>{reservation.title}</strong>
                    <span className="muted">
                      {reservation.customer_name || reservation.customer_email} · {dateTime(reservation.slot.starts_at)} · {reservation.status}
                      {reservation.attendance ? ` · ${reservation.attendance.status}` : ''}
                    </span>
                    {reservation.attendance?.checkin_token ? (
                      <small className="muted">QR token: {reservation.attendance.checkin_token}</small>
                    ) : null}
                    {reservation.status !== 'cancelled' && reservation.attendance?.status !== 'checked_in' && reservation.attendance?.status !== 'attended' ? (
                      <button type="button" className="button secondary" onClick={() => void checkIn(reservation.id)} disabled={saving}>
                        Check-in
                      </button>
                    ) : null}
                    {reservation.attendance?.status === 'checked_in' ? (
                      <button type="button" className="button secondary" onClick={() => void checkOut(reservation.attendance?.id || '')} disabled={saving}>
                        Check-out
                      </button>
                    ) : null}
                    {reservation.status !== 'cancelled' && reservation.attendance?.status !== 'attended' ? (
                      <button type="button" className="button ghost" onClick={() => void markNoShow(reservation.id)} disabled={saving}>
                        No-show
                      </button>
                    ) : null}
                    {reservation.status !== 'cancelled' ? (
                      <button type="button" className="button ghost" onClick={() => void cancelReservation(reservation.id)} disabled={saving}>
                        Cancel
                      </button>
                    ) : null}
                  </div>
                ))}
                {!state.reservations.length ? <p className="muted">Резерваций пока нет.</p> : null}
              </div>
            </div>

            <div className="card">
              <h3 className="title-md">Waitlist</h3>
              <div className="stack" style={{ gap: 10 }}>
                {state.waitlist.map((entry) => (
                  <div key={entry.id} className="list-item">
                    <strong>{entry.title || 'Waiting customer'}</strong>
                    <span className="muted">{entry.customer_name || entry.customer_email} · {dateTime(entry.slot.starts_at)} · {entry.status}</span>
                  </div>
                ))}
                {!state.waitlist.length ? <p className="muted">Waitlist пуст.</p> : null}
              </div>
            </div>
          </div>

          <div className="card">
            <h3 className="title-md">Attendance history</h3>
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Customer</th>
                    <th>Slot</th>
                    <th>Status</th>
                    <th>Method</th>
                    <th>Checked in</th>
                    <th>Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {state.attendance.map((item) => (
                    <tr key={item.id}>
                      <td>{item.customer_name || item.customer_email || '-'}</td>
                      <td>{dateTime(item.slot_starts_at)}</td>
                      <td><span className="badge secondary">{item.status}</span></td>
                      <td>{item.checkin_method}</td>
                      <td>{dateTime(item.checked_in_at)}</td>
                      <td>{Math.round((item.duration_seconds || 0) / 60)} min</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {!state.attendance.length ? <p className="muted">Истории посещений пока нет.</p> : null}
          </div>
        </>
      ) : null}
    </section>
  );
}
