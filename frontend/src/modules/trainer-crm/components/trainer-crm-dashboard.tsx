'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  DSDataTable,
  DSEmptyState,
  DSRichTextEditor,
  DSSection,
  DSSelect,
  DSSkeleton,
  DSStatsGrid,
  DSStatusDot,
  DSTextField,
  DSTransitionPanel,
} from '@/design-system';
import {
  trainerCrmApi,
  type TrainerCRMCustomer,
  type TrainerCRMDetail,
  type TrainerCRMSegment,
  type TrainerCRMSnapshot,
} from '@/modules/trainer-crm/api';

const DAY_OPTIONS = [30, 90, 180, 365];

function money(value?: string | number | null, currency = 'RUB') {
  const amount = Number(value ?? 0);
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency, maximumFractionDigits: 2 }).format(Number.isFinite(amount) ? amount : 0);
}

function dateTime(value?: string | null) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function CustomerTable({
  rows,
  selectedId,
  onSelect,
}: {
  rows: TrainerCRMCustomer[];
  selectedId?: string;
  onSelect: (customerId: string) => void;
}) {
  if (!rows.length) {
    return <DSEmptyState title="Клиенты пока не найдены" description="Попробуй изменить поиск или период CRM." />;
  }

  return (
    <DSDataTable
      columns={[
        { key: 'client', label: 'Client' },
        { key: 'revenue', label: 'Revenue' },
        { key: 'orders', label: 'Orders' },
        { key: 'access', label: 'Access' },
        { key: 'segments', label: 'Segments' },
        { key: 'lastOrder', label: 'Last order' },
      ]}
      rows={rows.map((customer) => ({
        client: (
          <button type="button" className="link-button" onClick={() => onSelect(customer.customer_id)}>
            <strong>{customer.display_name}</strong>
            <span className="muted" style={{ display: 'block' }}>{customer.email}</span>
          </button>
        ),
        revenue: money(customer.total_spent),
        orders: `${customer.paid_orders_count}/${customer.orders_count}`,
        access: <span className="badge secondary">{customer.active_entitlements_count} active</span>,
        segments: customer.segments.map((segment) => segment.name).join(', ') || '-',
        lastOrder: dateTime(customer.last_order_at),
        selected: selectedId === customer.customer_id ? 'selected' : '',
      }))}
      getRowKey={(row, index) => `${String(row.selected)}-${rows[index]?.customer_id || index}`}
    />
  );
}

function DetailPanel({
  detail,
  note,
  setNote,
  onCreateNote,
  selectedSegment,
  setSelectedSegment,
  onAssignSegment,
  allSegments,
  saving,
}: {
  detail: TrainerCRMDetail | null;
  note: string;
  setNote: (value: string) => void;
  onCreateNote: () => void;
  selectedSegment: string;
  setSelectedSegment: (value: string) => void;
  onAssignSegment: () => void;
  allSegments: TrainerCRMSegment[];
  saving: boolean;
}) {
  if (!detail) {
    return <DSEmptyState title="Выберите клиента" description="CRM-карточка откроется после выбора строки в таблице." />;
  }

  return (
    <DSTransitionPanel active className="stack" style={{ gap: 18 }}>
      <div className="card">
        <div className="stack" style={{ gap: 8 }}>
          <DSStatusDot tone={detail.customer.active_entitlements_count > 0 ? 'success' : 'neutral'} label={detail.customer.status} />
          <h2 className="title-md">{detail.customer.display_name}</h2>
          <p className="muted">{detail.customer.email}</p>
        </div>
        <div style={{ marginTop: 18 }}>
          <DSStatsGrid
            stats={[
              { label: 'Total spent', value: money(detail.customer.total_spent), tone: 'success' },
              { label: 'Orders', value: detail.customer.paid_orders_count, tone: 'primary' },
              { label: 'Access', value: detail.customer.active_entitlements_count, tone: detail.customer.active_entitlements_count > 0 ? 'success' : 'neutral' },
              { label: 'Notes', value: detail.customer.notes_count, tone: detail.customer.notes_count > 0 ? 'primary' : 'neutral' },
            ]}
          />
        </div>
      </div>

      <div className="grid-2">
        <DSSection title="Trainer notes" description="Внутренние заметки по клиенту.">
          <div className="card compact">
          <DSRichTextEditor label="New note" value={note} onChange={(event) => setNote(event.target.value)} rows={4} placeholder="Заметка тренера" />
          <button type="button" className="button secondary" onClick={onCreateNote} disabled={saving || !note.trim()} style={{ marginTop: 10 }}>
            Save note
          </button>
          <div className="stack" style={{ gap: 10, marginTop: 16 }}>
            {detail.notes.map((item) => (
              <div key={item.id} className="list-item">
                <strong>{item.pinned ? 'Pinned note' : 'Note'}</strong>
                <p className="muted">{item.body}</p>
                <small className="muted">{dateTime(item.created_at)}</small>
              </div>
            ))}
            {!detail.notes.length ? <DSEmptyState title="Заметок пока нет" description="Добавь первую заметку по клиенту." /> : null}
          </div>
          </div>
        </DSSection>

        <DSSection title="Segments" description="Назначение клиента в рабочий сегмент.">
          <div className="card compact">
          <DSSelect label="Segment" value={selectedSegment} onChange={(event) => setSelectedSegment(event.target.value)}>
            <option value="">Select segment</option>
            {allSegments.map((segment) => (
              <option key={segment.id} value={segment.id}>{segment.name}</option>
            ))}
          </DSSelect>
          <button type="button" className="button secondary" onClick={onAssignSegment} disabled={saving || !selectedSegment} style={{ marginTop: 10 }}>
            Assign segment
          </button>
          </div>
        </DSSection>
      </div>

      <div className="grid-2">
        <DSSection title="Purchase history" description="История заказов клиента.">
          <div className="card compact stack" style={{ gap: 10 }}>
            {detail.purchase_history.map((order) => (
              <div key={order.id} className="list-item">
                <strong>{money(order.total_amount, order.currency)}</strong>
                <span className="muted">{order.status} · {dateTime(order.created_at)}</span>
              </div>
            ))}
            {!detail.purchase_history.length ? <DSEmptyState title="Покупок пока нет" description="История появится после первого заказа." /> : null}
          </div>
        </DSSection>

        <DSSection title="Attendance / access" description="Посещения и выданные доступы.">
          <div className="card compact stack" style={{ gap: 10 }}>
            {detail.attendance_history.map((item) => (
              <div key={item.id} className="list-item">
                <strong>{item.title}</strong>
                <span className="muted">{item.status} · {dateTime(item.starts_at)}</span>
              </div>
            ))}
            {detail.access_history.slice(0, 8).map((item) => (
              <div key={item.id} className="list-item">
                <strong>{item.target_type}</strong>
                <span className="muted">{item.status} · {dateTime(item.created_at)}</span>
              </div>
            ))}
            {!detail.attendance_history.length && !detail.access_history.length ? <DSEmptyState title="Истории пока нет" description="Доступы и посещения появятся после активности клиента." /> : null}
          </div>
        </DSSection>
      </div>
    </DSTransitionPanel>
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
      setMessage(error instanceof Error ? error.message : 'Не удалось загрузить CRM');
    } finally {
      setLoading(false);
    }
  }

  async function selectCustomer(customerId: string) {
    setSelectedId(customerId);
    setDetail(await trainerCrmApi.getCustomer(customerId));
    setNote('');
    setSelectedSegment('');
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
    <section className="stack" style={{ gap: 24 }}>
      <DSSection
        title="Клиенты тренера"
        description="Карточка клиента, история покупок и доступов, заметки тренера и сегменты."
        actions={
          <>
            <DSTextField label="Search customer" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search customer" />
            <DSSelect label="Period" value={days} onChange={(event) => setDays(Number(event.target.value))}>
              {DAY_OPTIONS.map((option) => <option key={option} value={option}>{option} дней</option>)}
            </DSSelect>
            <button type="button" className="button secondary" onClick={() => void load(days, search)} disabled={loading}>Refresh</button>
          </>
        }
      >
        <span className="badge secondary">CRM Core</span>
      </DSSection>

      {message ? <div className="card error">{message}</div> : null}
      {loading && !snapshot ? <div className="card"><DSSkeleton lines={5} /></div> : null}

      {snapshot ? (
        <DSTransitionPanel active className="stack" style={{ gap: 24 }}>
          <DSStatsGrid
            stats={[
              { label: 'Customers', value: snapshot.summary.customers_count, tone: 'primary' },
              { label: 'Active access', value: snapshot.summary.with_active_access_count, tone: 'success' },
              { label: 'With notes', value: snapshot.summary.with_notes_count, tone: 'primary' },
              { label: 'Segments', value: snapshot.summary.segments_count, tone: 'warning' },
            ]}
          />

          <div className="grid-2">
            <DSSection title="Client segments" description="Рабочие сегменты для CRM-фильтрации.">
              <div className="card compact">
                <div className="row" style={{ gap: 12, alignItems: 'flex-end', marginBottom: 16 }}>
                  <div>
                    <span className="badge secondary">Segments</span>
                  </div>
                  <div className="inline" style={{ gap: 8 }}>
                    <input className="input" value={segmentName} onChange={(event) => setSegmentName(event.target.value)} placeholder="New segment" />
                    <button type="button" className="button secondary" onClick={() => void createSegment()} disabled={saving || !segmentName.trim()}>
                      Add
                    </button>
                  </div>
                </div>
                <div className="inline" style={{ gap: 8, flexWrap: 'wrap' }}>
                  {snapshot.segments.map((segment) => (
                    <span key={segment.id} className="badge secondary">{segment.name} · {segment.customers_count || 0}</span>
                  ))}
                  {!snapshot.segments.length ? <DSEmptyState title="Сегментов пока нет" description="Создай первый сегмент для группировки клиентов." /> : null}
                </div>
              </div>
            </DSSection>

            <DSSection title="CRM window" description={`Сводка считает выручку за ${snapshot.summary.period_days} дней, а карточка клиента показывает расширенную историю.`}>
              <div className="card compact">
                <DSStatusDot tone="primary" label={`${snapshot.summary.period_days} days`} />
              </div>
            </DSSection>
          </div>

          <DSSection title="Customer list" description="Выбор клиента открывает подробную CRM-карточку.">
            <div className="card compact">
              <CustomerTable rows={rows} selectedId={selectedId} onSelect={(id) => void selectCustomer(id)} />
            </div>
          </DSSection>

          <DetailPanel
            detail={detail}
            note={note}
            setNote={setNote}
            onCreateNote={() => void createNote()}
            selectedSegment={selectedSegment}
            setSelectedSegment={setSelectedSegment}
            onAssignSegment={() => void assignSegment()}
            allSegments={snapshot.segments}
            saving={saving}
          />
        </DSTransitionPanel>
      ) : null}
    </section>
  );
}
