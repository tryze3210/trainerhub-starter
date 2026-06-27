'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  DSCalendar,
  DSDataTable,
  DSEmptyState,
  DSSection,
  DSSelect,
  DSSkeleton,
  DSStatsGrid,
  DSStatusDot,
  DSTextField,
  DSTransitionPanel,
} from '@/design-system';
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

function RuleList({ rules }: { rules: AvailabilityRule[] }) {
  if (!rules.length) {
    return <DSEmptyState title="Правила не настроены" description="Добавь правило доступности, чтобы генерировать слоты." />;
  }

  return (
    <div className="stack" style={{ gap: 10 }}>
      {rules.map((rule) => (
        <div key={rule.id} className="list-item">
          <div className="row">
            <strong>{WEEKDAYS[rule.weekday] || rule.weekday}</strong>
            <DSStatusDot tone={rule.is_active ? 'success' : 'warning'} label={rule.is_active ? 'active' : 'paused'} />
          </div>
          <span className="muted">{minuteLabel(rule.start_minute)}-{minuteLabel(rule.end_minute)} · {rule.slot_size_minutes} min</span>
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
  const calendarEvents = useMemo(
    () =>
      upcomingSlots.slice(0, 24).map((slot) => ({
        id: slot.id,
        day: new Date(slot.starts_at).getDate(),
        title: `${minuteLabel(new Date(slot.starts_at).getHours() * 60 + new Date(slot.starts_at).getMinutes())} ${slot.status}`,
        tone: (slot.status === 'open' ? 'success' : slot.status === 'booked' ? 'warning' : 'neutral') as 'success' | 'warning' | 'neutral',
      })),
    [upcomingSlots],
  );

  return (
    <section className="stack" style={{ gap: 24 }}>
      <DSSection
        title="Расписание тренера"
        description="Доступность, генерация слотов, лимиты мест, отмены и waitlist."
        actions={
          <>
            <DSSelect label="Period" value={days} onChange={(event) => setDays(Number(event.target.value))}>
            {DAY_OPTIONS.map((option) => <option key={option} value={option}>{option} дней</option>)}
            </DSSelect>
            <button type="button" className="button secondary" onClick={() => void load()} disabled={loading}>
              Refresh
            </button>
          </>
        }
      >
        <span className="badge secondary">Booking / Schedule</span>
      </DSSection>

      {message ? <div className="card">{message}</div> : null}
      {loading && !state ? <div className="card"><DSSkeleton lines={5} /></div> : null}

      {state ? (
        <DSTransitionPanel active className="stack" style={{ gap: 24 }}>
          <DSStatsGrid
            stats={[
              { label: 'Slots', value: state.summary.slots_total, tone: 'primary' },
              { label: 'Open', value: state.summary.slots_open, tone: 'success' },
              { label: 'Reservations', value: state.summary.reservations_confirmed, tone: 'primary' },
              { label: 'Checked in', value: state.summary.attendance_checked_in, tone: 'success' },
            ]}
          />
          <DSStatsGrid
            columns={2}
            stats={[
              { label: 'No-show', value: state.summary.attendance_no_show, tone: state.summary.attendance_no_show > 0 ? 'warning' : 'success' },
              { label: 'Waitlist', value: state.summary.waitlist_waiting, tone: state.summary.waitlist_waiting > 0 ? 'warning' : 'neutral' },
            ]}
          />

          <DSSection title="Schedule calendar" description="Ближайшие слоты из текущего окна.">
            <DSCalendar monthLabel={`Next ${days} days`} days={31} events={calendarEvents} />
          </DSSection>

          <div className="grid-2">
            <DSSection title="Availability rules" description="Шаблоны доступности для генерации слотов.">
              <div className="card compact">
              <div className="grid-4" style={{ marginBottom: 16 }}>
                <DSSelect label="Weekday" value={weekday} onChange={(event) => setWeekday(Number(event.target.value))}>
                  {WEEKDAYS.map((label, index) => <option key={label} value={index}>{label}</option>)}
                </DSSelect>
                <DSTextField label="Start" type="time" value={startTime} onChange={(event) => setStartTime(event.target.value)} />
                <DSTextField label="End" type="time" value={endTime} onChange={(event) => setEndTime(event.target.value)} />
                <DSTextField label="Slot size" type="number" min={15} max={240} step={15} value={slotSize} onChange={(event) => setSlotSize(Number(event.target.value))} />
              </div>
              <button type="button" className="button secondary" onClick={() => void createRule()} disabled={saving}>
                Add rule
              </button>
              <div style={{ marginTop: 18 }}>
                <RuleList rules={rules} />
              </div>
              </div>
            </DSSection>

            <DSSection title="Generate slots" description="Создание слотов по правилам доступности.">
              <div className="card compact">
              <div className="grid-2" style={{ marginBottom: 16 }}>
                <DSTextField label="Start date" type="date" value={rangeStart} onChange={(event) => setRangeStart(event.target.value)} />
                <DSTextField label="End date" type="date" value={rangeEnd} onChange={(event) => setRangeEnd(event.target.value)} />
              </div>
              <button type="button" className="button secondary" onClick={() => void generateSlots()} disabled={saving}>
                Generate
              </button>
              <p className="muted" style={{ marginTop: 12 }}>Profile timezone: {state.profile.timezone}</p>
              </div>
            </DSSection>
          </div>

          <DSSection title="Slots" description="До 80 ближайших слотов в текущем окне.">
            <div className="card compact">
              {upcomingSlots.length ? (
                <DSDataTable
                  columns={[
                    { key: 'start', label: 'Start' },
                    { key: 'status', label: 'Status' },
                    { key: 'capacity', label: 'Capacity' },
                    { key: 'waitlist', label: 'Waitlist' },
                    { key: 'source', label: 'Source' },
                  ]}
                  rows={upcomingSlots.map((slot) => ({
                    start: dateTime(slot.starts_at),
                    status: <span className="badge secondary">{slot.status}</span>,
                    capacity: `${slot.reservations_count}/${slot.capacity}`,
                    waitlist: slot.waitlist_count,
                    source: slot.source,
                  }))}
                  getRowKey={(_, index) => upcomingSlots[index]?.id || String(index)}
                />
              ) : (
                <DSEmptyState title="Слотов пока нет" description="Сгенерируй слоты из правил доступности." />
              )}
            </div>
          </DSSection>

          <div className="grid-2">
            <DSSection title="Reservations" description="Бронирования и attendance-действия.">
              <div className="card compact">
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
                    <div className="inline" style={{ flexWrap: 'wrap' }}>
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
                  </div>
                ))}
                {!state.reservations.length ? <DSEmptyState title="Резерваций пока нет" description="Записи появятся после бронирования слотов." /> : null}
              </div>
              </div>
            </DSSection>

            <DSSection title="Waitlist" description="Очередь ожидания на занятые слоты.">
              <div className="card compact">
              <div className="stack" style={{ gap: 10 }}>
                {state.waitlist.map((entry) => (
                  <div key={entry.id} className="list-item">
                    <strong>{entry.title || 'Waiting customer'}</strong>
                    <span className="muted">{entry.customer_name || entry.customer_email} · {dateTime(entry.slot.starts_at)} · {entry.status}</span>
                  </div>
                ))}
                {!state.waitlist.length ? <DSEmptyState title="Waitlist пуст" description="Очередь ожидания сейчас не требует действий." /> : null}
              </div>
              </div>
            </DSSection>
          </div>

          <DSSection title="Attendance history" description="История check-in/check-out и длительность посещений.">
            <div className="card compact">
              {state.attendance.length ? (
                <DSDataTable
                  columns={[
                    { key: 'customer', label: 'Customer' },
                    { key: 'slot', label: 'Slot' },
                    { key: 'status', label: 'Status' },
                    { key: 'method', label: 'Method' },
                    { key: 'checkedIn', label: 'Checked in' },
                    { key: 'duration', label: 'Duration' },
                  ]}
                  rows={state.attendance.map((item) => ({
                    customer: item.customer_name || item.customer_email || '-',
                    slot: dateTime(item.slot_starts_at),
                    status: <span className="badge secondary">{item.status}</span>,
                    method: item.checkin_method,
                    checkedIn: dateTime(item.checked_in_at),
                    duration: `${Math.round((item.duration_seconds || 0) / 60)} min`,
                  }))}
                  getRowKey={(_, index) => state.attendance[index]?.id || String(index)}
                />
              ) : (
                <DSEmptyState title="Истории посещений пока нет" description="История появится после первого check-in." />
              )}
            </div>
          </DSSection>
        </DSTransitionPanel>
      ) : null}
    </section>
  );
}
