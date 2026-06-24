'use client';

import { useEffect, useMemo, useState } from 'react';
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

function CustomerTable({
  rows,
  selectedId,
  onSelect,
}: {
  rows: TrainerCRMCustomer[];
  selectedId?: string;
  onSelect: (customerId: string) => void;
}) {
  if (!rows.length) return <p className="muted">Клиенты пока не найдены.</p>;

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>Client</th>
            <th>Revenue</th>
            <th>Orders</th>
            <th>Access</th>
            <th>Segments</th>
            <th>Last order</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((customer) => (
            <tr key={customer.customer_id} className={selectedId === customer.customer_id ? 'is-active' : ''}>
              <td>
                <button type="button" className="link-button" onClick={() => onSelect(customer.customer_id)}>
                  <strong>{customer.display_name}</strong>
                </button>
                <div className="muted">{customer.email}</div>
              </td>
              <td>{money(customer.total_spent)}</td>
              <td>{customer.paid_orders_count}/{customer.orders_count}</td>
              <td><span className="badge secondary">{customer.active_entitlements_count} active</span></td>
              <td>{customer.segments.map((segment) => segment.name).join(', ') || '-'}</td>
              <td>{dateTime(customer.last_order_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
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
  if (!detail) return <div className="card">Выберите клиента, чтобы открыть CRM-карточку.</div>;

  return (
    <div className="stack" style={{ gap: 18 }}>
      <div className="card">
        <div className="stack" style={{ gap: 8 }}>
          <span className="badge secondary">{detail.customer.status}</span>
          <h2 className="title-md">{detail.customer.display_name}</h2>
          <p className="muted">{detail.customer.email}</p>
        </div>
        <div className="grid-4" style={{ marginTop: 18 }}>
          <StatCard title="Total spent" value={money(detail.customer.total_spent)} />
          <StatCard title="Orders" value={detail.customer.paid_orders_count} />
          <StatCard title="Access" value={detail.customer.active_entitlements_count} />
          <StatCard title="Notes" value={detail.customer.notes_count} />
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <h3 className="title-md">Trainer notes</h3>
          <textarea className="input" value={note} onChange={(event) => setNote(event.target.value)} rows={4} placeholder="Заметка тренера" />
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
            {!detail.notes.length ? <p className="muted">Заметок пока нет.</p> : null}
          </div>
        </div>

        <div className="card">
          <h3 className="title-md">Segments</h3>
          <select className="input" value={selectedSegment} onChange={(event) => setSelectedSegment(event.target.value)}>
            <option value="">Select segment</option>
            {allSegments.map((segment) => (
              <option key={segment.id} value={segment.id}>{segment.name}</option>
            ))}
          </select>
          <button type="button" className="button secondary" onClick={onAssignSegment} disabled={saving || !selectedSegment} style={{ marginTop: 10 }}>
            Assign segment
          </button>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <h3 className="title-md">Purchase history</h3>
          <div className="stack" style={{ gap: 10 }}>
            {detail.purchase_history.map((order) => (
              <div key={order.id} className="list-item">
                <strong>{money(order.total_amount, order.currency)}</strong>
                <span className="muted">{order.status} · {dateTime(order.created_at)}</span>
              </div>
            ))}
            {!detail.purchase_history.length ? <p className="muted">Покупок пока нет.</p> : null}
          </div>
        </div>

        <div className="card">
          <h3 className="title-md">Attendance / access</h3>
          <div className="stack" style={{ gap: 10 }}>
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
            {!detail.attendance_history.length && !detail.access_history.length ? <p className="muted">Истории пока нет.</p> : null}
          </div>
        </div>
      </div>
    </div>
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
      <div className="card row" style={{ gap: 16, alignItems: 'flex-end' }}>
        <div className="stack" style={{ gap: 8 }}>
          <span className="badge secondary">CRM Core</span>
          <h2 className="title-md">Клиенты тренера</h2>
          <p className="muted">Карточка клиента, история покупок и доступов, заметки тренера и сегменты.</p>
        </div>
        <div className="inline" style={{ gap: 10, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
          <input className="input" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search customer" />
          <select className="input" value={days} onChange={(event) => setDays(Number(event.target.value))}>
            {DAY_OPTIONS.map((option) => <option key={option} value={option}>{option} дней</option>)}
          </select>
          <button type="button" className="button secondary" onClick={() => void load(days, search)} disabled={loading}>Refresh</button>
        </div>
      </div>

      {message ? <div className="card error">{message}</div> : null}
      {loading && !snapshot ? <div className="card">Загрузка CRM...</div> : null}

      {snapshot ? (
        <>
          <div className="grid-4">
            <StatCard title="Customers" value={snapshot.summary.customers_count} />
            <StatCard title="Active access" value={snapshot.summary.with_active_access_count} />
            <StatCard title="With notes" value={snapshot.summary.with_notes_count} />
            <StatCard title="Segments" value={snapshot.summary.segments_count} />
          </div>

          <div className="grid-2">
            <div className="card">
              <div className="row" style={{ gap: 12, alignItems: 'flex-end', marginBottom: 16 }}>
                <div>
                  <span className="badge secondary">Segments</span>
                  <h3 className="title-md">Client segments</h3>
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
                {!snapshot.segments.length ? <span className="muted">Сегментов пока нет.</span> : null}
              </div>
            </div>

            <div className="card">
              <span className="badge secondary">Period</span>
              <h3 className="title-md">CRM window</h3>
              <p className="muted">Сводка считает выручку за {snapshot.summary.period_days} дней, а карточка клиента показывает расширенную историю.</p>
            </div>
          </div>

          <div className="card">
            <h3 className="title-md">Customer list</h3>
            <CustomerTable rows={rows} selectedId={selectedId} onSelect={(id) => void selectCustomer(id)} />
          </div>

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
        </>
      ) : null}
    </section>
  );
}
