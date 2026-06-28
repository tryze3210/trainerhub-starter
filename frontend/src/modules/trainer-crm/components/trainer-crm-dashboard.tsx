'use client';

import { useEffect, useMemo, useState } from 'react';

import {
  trainerCrmApi,
  type TrainerCRMCustomer,
  type TrainerCRMDetail,
  type TrainerCRMSegment,
  type TrainerCRMSnapshot,
} from '@/modules/trainer-crm/api';
import { trainerOperationStatusLabel, trainerOperationStatusTone } from '@/modules/trainer-operations/format';

const DAY_OPTIONS = [30, 90, 180, 365];

function money(value?: string | number | null, currency = 'RUB') {
  const amount = Number(value ?? 0);
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency, maximumFractionDigits: 2 }).format(Number.isFinite(amount) ? amount : 0);
}

function dateTime(value?: string | null) {
  if (!value) return 'Дата не указана';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function statusClass(value?: string | null) {
  return `trainer-operations-status trainer-operations-status-${trainerOperationStatusTone(value)}`;
}

function CustomerRail({
  rows,
  selectedId,
  onSelect,
}: {
  rows: TrainerCRMCustomer[];
  selectedId?: string;
  onSelect: (customerId: string) => void;
}) {
  if (!rows.length) {
    return (
      <div className="trainer-operations-empty">
        <strong>Ученики пока не найдены</strong>
        <p>Когда ученик купит продукт или получит доступ, он появится здесь.</p>
      </div>
    );
  }

  return (
    <div className="trainer-operations-rail" aria-label="Ученики">
      {rows.map((customer) => (
        <button
          className={selectedId === customer.customer_id ? 'trainer-operations-card trainer-operations-card-active' : 'trainer-operations-card'}
          key={customer.customer_id}
          type="button"
          onClick={() => onSelect(customer.customer_id)}
        >
          <span className={statusClass(customer.status)}>{trainerOperationStatusLabel(customer.status)}</span>
          <strong>{customer.display_name || customer.email}</strong>
          <span>{customer.email}</span>
          <span>{money(customer.total_spent)} потрачено</span>
          <span>{customer.paid_orders_count} оплаченных из {customer.orders_count} заказов</span>
          <span>{customer.active_entitlements_count} активных доступов</span>
          <small>{customer.segments.map((segment) => segment.name).join(', ') || 'Без сегмента'}</small>
        </button>
      ))}
    </div>
  );
}

function DetailPanel({ detail }: { detail: TrainerCRMDetail | null }) {
  if (!detail) {
    return (
      <section className="trainer-operations-detail-panel">
        <h3>Выберите ученика</h3>
        <p>Откройте карточку ученика из ленты, чтобы увидеть покупки, доступы, заметки и посещения.</p>
      </section>
    );
  }

  return (
    <section className="trainer-operations-detail-panel">
      <header className="trainer-operations-section-header">
        <div>
          <h3>Профиль ученика</h3>
          <p>{detail.customer.display_name || detail.customer.email}</p>
        </div>
        <span className={statusClass(detail.customer.status)}>{trainerOperationStatusLabel(detail.customer.status)}</span>
      </header>

      <section className="trainer-operations-metrics" aria-label="Показатели ученика">
        <div className="trainer-operations-metric"><span>Потрачено</span><strong>{money(detail.customer.total_spent)}</strong></div>
        <div className="trainer-operations-metric"><span>Заказы</span><strong>{detail.customer.paid_orders_count}</strong></div>
        <div className="trainer-operations-metric"><span>Активные доступы</span><strong>{detail.customer.active_entitlements_count}</strong></div>
        <div className="trainer-operations-metric"><span>Заметки</span><strong>{detail.customer.notes_count}</strong></div>
      </section>

      <div className="trainer-operations-support-panels">
        <article className="trainer-operations-panel">
          <h4>Контакты</h4>
          <div className="trainer-operations-row-list">
            <div className="trainer-operations-row"><div><strong>Email</strong><span>{detail.customer.email}</span></div></div>
            <div className="trainer-operations-row"><div><strong>Сегменты</strong><span>{detail.segments.map((segment) => segment.name).join(', ') || 'Не назначены'}</span></div></div>
            <div className="trainer-operations-row"><div><strong>Последний заказ</strong><span>{dateTime(detail.customer.last_order_at)}</span></div></div>
          </div>
        </article>

        <article className="trainer-operations-panel">
          <h4>Покупки</h4>
          <div className="trainer-operations-row-list">
            {detail.purchase_history.slice(0, 8).map((order) => (
              <div className="trainer-operations-row" key={order.id}>
                <div>
                  <strong>{money(order.total_amount, order.currency)}</strong>
                  <span>{trainerOperationStatusLabel(order.status)} · {dateTime(order.created_at)}</span>
                </div>
                <span className={statusClass(order.status)}>{order.items_count} позиций</span>
              </div>
            ))}
            {!detail.purchase_history.length ? <div className="trainer-operations-empty"><strong>Покупок пока нет</strong><p>История появится после первого заказа.</p></div> : null}
          </div>
        </article>
      </div>

      <div className="trainer-operations-support-panels">
        <article className="trainer-operations-panel">
          <h4>Доступы</h4>
          <div className="trainer-operations-row-list">
            {detail.access_history.slice(0, 8).map((item) => (
              <div className="trainer-operations-row" key={item.id}>
                <div>
                  <strong>Доступ к материалу</strong>
                  <span>{trainerOperationStatusLabel(item.status)} · выдан {dateTime(item.created_at)}</span>
                </div>
                <span className={statusClass(item.status)}>{trainerOperationStatusLabel(item.status)}</span>
              </div>
            ))}
            {!detail.access_history.length ? <div className="trainer-operations-empty"><strong>Доступов пока нет</strong><p>Доступы появятся после покупки или ручной выдачи.</p></div> : null}
          </div>
        </article>

        <article className="trainer-operations-panel">
          <h4>Посещения</h4>
          <div className="trainer-operations-row-list">
            {detail.attendance_history.slice(0, 8).map((item) => (
              <div className="trainer-operations-row" key={item.id}>
                <div>
                  <strong>{item.title || 'Занятие'}</strong>
                  <span>{trainerOperationStatusLabel(item.status)} · {dateTime(item.starts_at)}</span>
                </div>
                <span className={statusClass(item.status)}>{trainerOperationStatusLabel(item.status)}</span>
              </div>
            ))}
            {!detail.attendance_history.length ? <div className="trainer-operations-empty"><strong>Посещений пока нет</strong><p>История появится после записи и отметки посещения.</p></div> : null}
          </div>
        </article>
      </div>
    </section>
  );
}

function NotesPanel({
  detail,
  note,
  setNote,
  onCreateNote,
  saving,
}: {
  detail: TrainerCRMDetail | null;
  note: string;
  setNote: (value: string) => void;
  onCreateNote: () => void;
  saving: boolean;
}) {
  return (
    <article className="trainer-operations-panel">
      <h3>Заметки тренера</h3>
      <label className="trainer-operations-field">
        <span>Заметка</span>
        <textarea
          value={note}
          onChange={(event) => setNote(event.target.value)}
          rows={4}
          placeholder="Напишите заметку о прогрессе, целях или договорённостях."
        />
      </label>
      <div className="trainer-operations-actions">
        <button type="button" className="premium-secondary-button" onClick={onCreateNote} disabled={saving || !detail || !note.trim()}>
          Сохранить заметку
        </button>
      </div>
      <div className="trainer-operations-row-list">
        {detail?.notes.map((item) => (
          <div className="trainer-operations-row" key={item.id}>
            <div>
              <strong>{item.pinned ? 'Закреплённая заметка' : 'Заметка'}</strong>
              <p>{item.body}</p>
              <small>{dateTime(item.created_at)}</small>
            </div>
          </div>
        ))}
        {!detail?.notes.length ? (
          <div className="trainer-operations-empty">
            <strong>Заметок пока нет</strong>
            <p>Добавьте первую заметку, чтобы фиксировать контекст работы с учеником.</p>
          </div>
        ) : null}
      </div>
    </article>
  );
}

function SegmentsPanel({
  segments,
  segmentName,
  setSegmentName,
  selectedSegment,
  setSelectedSegment,
  onCreateSegment,
  onAssignSegment,
  saving,
  canAssign,
}: {
  segments: TrainerCRMSegment[];
  segmentName: string;
  setSegmentName: (value: string) => void;
  selectedSegment: string;
  setSelectedSegment: (value: string) => void;
  onCreateSegment: () => void;
  onAssignSegment: () => void;
  saving: boolean;
  canAssign: boolean;
}) {
  return (
    <article className="trainer-operations-panel">
      <h3>Сегменты</h3>
      <div className="trainer-operations-toolbar-fields">
        <label className="trainer-operations-field">
          <span>Новый сегмент</span>
          <input value={segmentName} onChange={(event) => setSegmentName(event.target.value)} placeholder="Например: регулярные ученики" />
        </label>
        <label className="trainer-operations-field">
          <span>Выберите сегмент</span>
          <select value={selectedSegment} onChange={(event) => setSelectedSegment(event.target.value)}>
            <option value="">Выберите сегмент</option>
            {segments.map((segment) => (
              <option key={segment.id} value={segment.id}>{segment.name}</option>
            ))}
          </select>
        </label>
      </div>
      <div className="trainer-operations-actions">
        <button type="button" className="premium-secondary-button" onClick={onCreateSegment} disabled={saving || !segmentName.trim()}>
          Создать сегмент
        </button>
        <button type="button" className="premium-secondary-button" onClick={onAssignSegment} disabled={saving || !canAssign || !selectedSegment}>
          Назначить сегмент
        </button>
      </div>
      <div className="trainer-operations-row-list">
        {segments.map((segment) => (
          <div className="trainer-operations-row" key={segment.id}>
            <div>
              <strong>{segment.name}</strong>
              <span>{segment.customers_count || 0} учеников</span>
            </div>
          </div>
        ))}
        {!segments.length ? <div className="trainer-operations-empty"><strong>Сегментов пока нет</strong><p>Создайте первый сегмент для группировки учеников.</p></div> : null}
      </div>
    </article>
  );
}

export function TrainerCRMDashboard() {
  const [days, setDays] = useState(90);
  const [search, setSearch] = useState('');
  const [snapshot, setSnapshot] = useState<TrainerCRMSnapshot | null>(null);
  const [detail, setDetail] = useState<TrainerCRMDetail | null>(null);
  const [selectedId, setSelectedId] = useState('');
  const [note, setNote] = useState('');
  const [segmentName, setSegmentName] = useState('');
  const [selectedSegment, setSelectedSegment] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  async function selectCustomer(customerId: string) {
    setSelectedId(customerId);
    setDetail(await trainerCrmApi.getCustomer(customerId));
    setNote('');
    setSelectedSegment('');
  }

  async function load(selectedDays = days, selectedSearch = search) {
    try {
      setLoading(true);
      setMessage('');
      const data = await trainerCrmApi.getSnapshot(selectedDays, selectedSearch);
      setSnapshot(data);
      if (!selectedId && data.items[0]) {
        await selectCustomer(data.items[0].customer_id);
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Не удалось загрузить учеников');
    } finally {
      setLoading(false);
    }
  }

  async function createNote() {
    if (!selectedId || !note.trim()) return;
    try {
      setSaving(true);
      await trainerCrmApi.createNote(selectedId, note.trim());
      await selectCustomer(selectedId);
      await load(days, search);
    } finally {
      setSaving(false);
    }
  }

  async function createSegment() {
    if (!segmentName.trim()) return;
    try {
      setSaving(true);
      await trainerCrmApi.createSegment(segmentName.trim());
      setSegmentName('');
      await load(days, search);
    } finally {
      setSaving(false);
    }
  }

  async function assignSegment() {
    if (!selectedId || !selectedSegment) return;
    try {
      setSaving(true);
      await trainerCrmApi.assignSegment(selectedId, selectedSegment);
      await selectCustomer(selectedId);
      await load(days, search);
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => {
    void load(days, search);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days]);

  const rows = useMemo(() => snapshot?.items || [], [snapshot?.items]);

  return (
    <section className="trainer-operations-page trainer-crm-page">
      <section className="trainer-operations-toolbar">
        <div>
          <h2>Ученики</h2>
          <p>Сегменты, заметки, покупки и активность учеников в одном рабочем пространстве.</p>
        </div>
        <div className="trainer-operations-toolbar-fields">
          <label className="trainer-operations-field">
            <span>Поиск ученика</span>
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Имя, email или сегмент" />
          </label>
          <label className="trainer-operations-field">
            <span>Период</span>
            <select value={days} onChange={(event) => setDays(Number(event.target.value))}>
              {DAY_OPTIONS.map((option) => <option key={option} value={option}>{option} дней</option>)}
            </select>
          </label>
          <button type="button" className="premium-secondary-button" onClick={() => void load(days, search)} disabled={loading}>
            Обновить
          </button>
        </div>
      </section>

      {message ? <div className="trainer-operations-message"><strong>Не удалось выполнить действие</strong><p>{message}</p></div> : null}
      {loading && !snapshot ? <div className="trainer-operations-message"><strong>Загружаем учеников</strong><p>Собираем покупки, доступы и заметки.</p></div> : null}

      {snapshot ? (
        <>
          <section className="trainer-operations-metrics" aria-label="Метрики учеников">
            <div className="trainer-operations-metric"><span>Ученики</span><strong>{snapshot.summary.customers_count}</strong></div>
            <div className="trainer-operations-metric"><span>С активным доступом</span><strong>{snapshot.summary.with_active_access_count}</strong></div>
            <div className="trainer-operations-metric"><span>С заметками</span><strong>{snapshot.summary.with_notes_count}</strong></div>
            <div className="trainer-operations-metric"><span>Сегменты</span><strong>{snapshot.summary.segments_count}</strong></div>
            <div className="trainer-operations-metric"><span>Период</span><strong>{snapshot.summary.period_days} дней</strong></div>
          </section>

          <section className="trainer-operations-rail-section">
            <header className="trainer-operations-section-header">
              <div>
                <h3>Лента учеников</h3>
                <p>Выберите ученика, чтобы открыть профиль, покупки, доступы и историю посещений.</p>
              </div>
            </header>
            <CustomerRail rows={rows} selectedId={selectedId} onSelect={(id) => void selectCustomer(id)} />
          </section>

          <DetailPanel detail={detail} />

          <section className="trainer-operations-support-panels">
            <NotesPanel detail={detail} note={note} setNote={setNote} onCreateNote={() => void createNote()} saving={saving} />
            <SegmentsPanel
              segments={snapshot.segments}
              segmentName={segmentName}
              setSegmentName={setSegmentName}
              selectedSegment={selectedSegment}
              setSelectedSegment={setSelectedSegment}
              onCreateSegment={() => void createSegment()}
              onAssignSegment={() => void assignSegment()}
              saving={saving}
              canAssign={Boolean(selectedId)}
            />
          </section>
        </>
      ) : null}
    </section>
  );
}
