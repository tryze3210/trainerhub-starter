'use client';

import { useEffect, useMemo, useState } from 'react';

import { trainerBookingApi, type AvailabilityRule, type TrainerBookingSchedule } from '@/modules/trainer-booking/api';
import { trainerOperationStatusLabel, trainerOperationStatusTone } from '@/modules/trainer-operations/format';

const DAY_OPTIONS = [14, 30, 60, 90];
const WEEKDAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

function dateTime(value?: string | null) {
  if (!value) return 'Дата не указана';
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

function statusClass(value?: string | null) {
  return `trainer-operations-status trainer-operations-status-${trainerOperationStatusTone(value)}`;
}

function minutesDuration(seconds?: number | null) {
  return `${Math.round((seconds || 0) / 60)} минут`;
}

function RuleList({ rules }: { rules: AvailabilityRule[] }) {
  if (!rules.length) {
    return (
      <div className="trainer-operations-empty">
        <strong>Правила ещё не настроены</strong>
        <p>Добавьте рабочие часы, чтобы создать слоты для записи.</p>
      </div>
    );
  }

  return (
    <div className="trainer-operations-row-list">
      {rules.map((rule) => (
        <div key={rule.id} className="trainer-operations-row">
          <div>
            <strong>{WEEKDAYS[rule.weekday] || String(rule.weekday)}</strong>
            <span>{minuteLabel(rule.start_minute)}–{minuteLabel(rule.end_minute)} · {rule.slot_size_minutes} минут</span>
          </div>
          <span className={statusClass(rule.is_active ? 'active' : 'inactive')}>
            {rule.is_active ? 'Активно' : 'На паузе'}
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
      setMessage(`Слоты созданы: ${result.created} новых, ${result.existing} уже существовали.`);
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
    <section className="trainer-operations-page trainer-schedule-page">
      <section className="trainer-operations-toolbar">
        <div>
          <h2>Расписание</h2>
          <p>Настраивайте рабочие часы, создавайте слоты, ведите записи и посещаемость.</p>
        </div>
        <div className="trainer-operations-toolbar-fields">
          <label className="trainer-operations-field">
            <span>Период</span>
            <select value={days} onChange={(event) => setDays(Number(event.target.value))}>
              {DAY_OPTIONS.map((option) => <option key={option} value={option}>{option} дней</option>)}
            </select>
          </label>
          <button type="button" className="premium-secondary-button" onClick={() => void load()} disabled={loading}>
            Обновить
          </button>
        </div>
      </section>

      {message ? <div className="trainer-operations-message"><strong>Статус расписания</strong><p>{message}</p></div> : null}
      {loading && !state ? <div className="trainer-operations-message"><strong>Загружаем расписание</strong><p>Получаем слоты, записи и посещения.</p></div> : null}

      {state ? (
        <>
          <section className="trainer-operations-metrics" aria-label="Метрики расписания">
            <div className="trainer-operations-metric"><span>Слоты</span><strong>{state.summary.slots_total}</strong></div>
            <div className="trainer-operations-metric"><span>Свободно</span><strong>{state.summary.slots_open}</strong></div>
            <div className="trainer-operations-metric"><span>Записи</span><strong>{state.summary.reservations_confirmed}</strong></div>
            <div className="trainer-operations-metric"><span>На занятии</span><strong>{state.summary.attendance_checked_in}</strong></div>
            <div className="trainer-operations-metric"><span>Не пришли</span><strong>{state.summary.attendance_no_show}</strong></div>
            <div className="trainer-operations-metric"><span>Лист ожидания</span><strong>{state.summary.waitlist_waiting}</strong></div>
          </section>

          <section className="trainer-operations-support-panels">
            <article className="trainer-operations-panel">
              <h3>Правила доступности</h3>
              <div className="trainer-operations-toolbar-fields">
                <label className="trainer-operations-field">
                  <span>День недели</span>
                  <select value={weekday} onChange={(event) => setWeekday(Number(event.target.value))}>
                    {WEEKDAYS.map((label, index) => <option key={label} value={index}>{label}</option>)}
                  </select>
                </label>
                <label className="trainer-operations-field">
                  <span>Начало</span>
                  <input type="time" value={startTime} onChange={(event) => setStartTime(event.target.value)} />
                </label>
                <label className="trainer-operations-field">
                  <span>Конец</span>
                  <input type="time" value={endTime} onChange={(event) => setEndTime(event.target.value)} />
                </label>
                <label className="trainer-operations-field">
                  <span>Длительность слота</span>
                  <input type="number" min={15} max={240} step={15} value={slotSize} onChange={(event) => setSlotSize(Number(event.target.value))} />
                </label>
              </div>
              <div className="trainer-operations-actions">
                <button type="button" className="premium-secondary-button" onClick={() => void createRule()} disabled={saving}>
                  Добавить правило
                </button>
              </div>
              <RuleList rules={rules} />
            </article>

            <article className="trainer-operations-panel">
              <h3>Создание слотов</h3>
              <div className="trainer-operations-toolbar-fields">
                <label className="trainer-operations-field">
                  <span>Дата начала</span>
                  <input type="date" value={rangeStart} onChange={(event) => setRangeStart(event.target.value)} />
                </label>
                <label className="trainer-operations-field">
                  <span>Дата окончания</span>
                  <input type="date" value={rangeEnd} onChange={(event) => setRangeEnd(event.target.value)} />
                </label>
              </div>
              <div className="trainer-operations-actions">
                <button type="button" className="premium-secondary-button" onClick={() => void generateSlots()} disabled={saving}>
                  Создать слоты
                </button>
              </div>
              <p>Часовой пояс: {state.profile.timezone}</p>
            </article>
          </section>

          <section className="trainer-operations-rail-section">
            <header className="trainer-operations-section-header">
              <div>
                <h3>Ближайшие слоты</h3>
                <p>До 80 ближайших слотов в выбранном периоде.</p>
              </div>
            </header>
            {upcomingSlots.length ? (
              <div className="trainer-operations-rail" aria-label="Ближайшие слоты">
                {upcomingSlots.map((slot) => (
                  <article className="trainer-operations-card" key={slot.id}>
                    <span className={statusClass(slot.status)}>{trainerOperationStatusLabel(slot.status)}</span>
                    <strong>{dateTime(slot.starts_at)}</strong>
                    <span>Места: {slot.reservations_count} / {slot.capacity}</span>
                    <span>Лист ожидания: {slot.waitlist_count}</span>
                    {slot.source && slot.source !== 'generated' ? <small>Источник: {slot.source}</small> : null}
                  </article>
                ))}
              </div>
            ) : (
              <div className="trainer-operations-empty">
                <strong>Слотов пока нет</strong>
                <p>Создайте слоты по правилам доступности.</p>
              </div>
            )}
          </section>

          <section className="trainer-operations-detail-panel">
            <header className="trainer-operations-section-header">
              <div>
                <h3>Записи учеников</h3>
                <p>Записи, статусы посещений и действия тренера.</p>
              </div>
            </header>
            <div className="trainer-operations-row-list">
              {state.reservations.map((reservation) => (
                <div className="trainer-operations-row" key={reservation.id}>
                  <div>
                    <strong>{reservation.title || 'Занятие'}</strong>
                    <span>{reservation.customer_name || reservation.customer_email || 'Ученик'} · {dateTime(reservation.slot.starts_at)}</span>
                    <span>{trainerOperationStatusLabel(reservation.status)}{reservation.attendance ? ` · ${trainerOperationStatusLabel(reservation.attendance.status)}` : ''}</span>
                    {reservation.attendance?.checkin_token ? <small>Код отметки доступен</small> : null}
                  </div>
                  <div className="trainer-operations-actions">
                    {reservation.status !== 'cancelled' && reservation.attendance?.status !== 'checked_in' && reservation.attendance?.status !== 'attended' ? (
                      <button type="button" className="premium-secondary-button" onClick={() => void checkIn(reservation.id)} disabled={saving}>
                        Отметить приход
                      </button>
                    ) : null}
                    {reservation.attendance?.status === 'checked_in' ? (
                      <button type="button" className="premium-secondary-button" onClick={() => void checkOut(reservation.attendance?.id || '')} disabled={saving}>
                        Завершить посещение
                      </button>
                    ) : null}
                    {reservation.status !== 'cancelled' && reservation.attendance?.status !== 'attended' ? (
                      <button type="button" className="premium-secondary-button" onClick={() => void markNoShow(reservation.id)} disabled={saving}>
                        Не пришёл
                      </button>
                    ) : null}
                    {reservation.status !== 'cancelled' ? (
                      <button type="button" className="premium-secondary-button" onClick={() => void cancelReservation(reservation.id)} disabled={saving}>
                        Отменить
                      </button>
                    ) : null}
                  </div>
                </div>
              ))}
              {!state.reservations.length ? <div className="trainer-operations-empty"><strong>Записей пока нет</strong><p>Записи появятся после бронирования слотов.</p></div> : null}
            </div>
          </section>

          <section className="trainer-operations-support-panels">
            <article className="trainer-operations-panel">
              <h3>Посещения</h3>
              <div className="trainer-operations-row-list">
                {state.attendance.map((item) => (
                  <div className="trainer-operations-row" key={item.id}>
                    <div>
                      <strong>{item.customer_name || item.customer_email || 'Ученик'}</strong>
                      <span>{dateTime(item.slot_starts_at)} · {trainerOperationStatusLabel(item.status)}</span>
                      <small>Метод отметки: {item.checkin_method || 'ручной'} · длительность {minutesDuration(item.duration_seconds)}</small>
                    </div>
                    <span className={statusClass(item.status)}>{trainerOperationStatusLabel(item.status)}</span>
                  </div>
                ))}
                {!state.attendance.length ? <div className="trainer-operations-empty"><strong>Посещений пока нет</strong><p>История появится после первой отметки прихода.</p></div> : null}
              </div>
            </article>

            <article className="trainer-operations-panel">
              <h3>Лист ожидания</h3>
              <div className="trainer-operations-row-list">
                {state.waitlist.map((entry) => (
                  <div className="trainer-operations-row" key={entry.id}>
                    <div>
                      <strong>{entry.title || 'Ученик в ожидании'}</strong>
                      <span>{entry.customer_name || entry.customer_email || 'Ученик'} · {dateTime(entry.slot.starts_at)}</span>
                    </div>
                    <span className={statusClass(entry.status)}>{trainerOperationStatusLabel(entry.status)}</span>
                  </div>
                ))}
                {!state.waitlist.length ? <div className="trainer-operations-empty"><strong>Лист ожидания пуст</strong><p>Очередь ожидания сейчас не требует действий.</p></div> : null}
              </div>
            </article>
          </section>
        </>
      ) : null}
    </section>
  );
}
