'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { subscriptionsApi, type AdminSubscriptionOverview, type SubscriptionItem } from '@/modules/subscriptions/api';

function formatMoney(value?: string | number, currency = 'RUB'): string {
  if (value === undefined || value === null || value === '') return `0 ${currency}`;
  return `${value} ${currency}`;
}

function formatDate(value?: string | null): string {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function statusClass(status?: string): string {
  if (status === 'active') return 'badge success';
  if (status === 'pending') return 'badge warning';
  if (status === 'past_due' || status === 'cancelled' || status === 'expired') return 'badge danger';
  return 'badge secondary';
}

export default function AdminSubscriptionsPage() {
  const [overview, setOverview] = useState<AdminSubscriptionOverview | null>(null);
  const [items, setItems] = useState<SubscriptionItem[]>([]);
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');
  const [msg, setMsg] = useState('');
  const [loading, setLoading] = useState(true);

  async function load() {
    try {
      setLoading(true);
      setMsg('');
      const [nextOverview, nextItems] = await Promise.all([
        subscriptionsApi.getAdminOverview(30),
        subscriptionsApi.listAdminItems({ status: status || undefined, search: search || undefined, limit: 100 }),
      ]);
      setOverview(nextOverview);
      setItems(nextItems);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить admin subscriptions');
    } finally {
      setLoading(false);
    }
  }

  async function expireDue() {
    try {
      const result = await subscriptionsApi.expireDue();
      setMsg(`Expired subscriptions: ${result.expired_count}`);
      await load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось выполнить expire-due');
    }
  }

  async function markPastDue(id: string) {
    try {
      await subscriptionsApi.markPastDue(id, 'admin_manual_action');
      await load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось пометить past_due');
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const summary = overview?.summary;
  const statusRows = useMemo(() => Object.entries(overview?.status_breakdown || {}), [overview]);

  return (
    <ProtectedPage title="Admin subscriptions" description="Операционный центр подписок платформы.">
      <section className="stack" style={{ gap: 28 }}>
        <div className="row" style={{ alignItems: 'flex-start' }}>
          <div className="stack" style={{ gap: 10 }}>
            <span className="badge success">Subscription ops</span>
            <h1>Admin subscriptions</h1>
            <p className="lead">
              Контроль recurring revenue: активные подписки, churn, due soon,
              проблемные оплаты, ручные операции и expire maintenance.
            </p>
          </div>
          <div className="inline">
            <button className="button secondary" onClick={() => void load()}>Обновить</button>
            <button className="button warning" onClick={() => void expireDue()}>Expire due</button>
            <Link className="button ghost" href="/admin/marketplace">Marketplace</Link>
          </div>
        </div>

        <div className="grid-4">
          <div className="card"><div className="kpi"><span className="muted">Active</span><strong>{summary?.active_count ?? 0}</strong></div></div>
          <div className="card"><div className="kpi"><span className="muted">MRR estimate</span><strong>{formatMoney(summary?.estimated_mrr, summary?.currency || 'RUB')}</strong></div></div>
          <div className="card"><div className="kpi"><span className="muted">Past due</span><strong>{summary?.past_due_count ?? 0}</strong></div></div>
          <div className="card"><div className="kpi"><span className="muted">Due soon</span><strong>{summary?.due_soon_count ?? 0}</strong></div></div>
        </div>

        <div className="grid-4">
          <div className="card compact"><div className="kpi"><span className="muted">New 30d</span><strong>{summary?.new_count ?? 0}</strong></div></div>
          <div className="card compact"><div className="kpi"><span className="muted">Revenue 30d</span><strong>{formatMoney(summary?.subscription_revenue, summary?.currency || 'RUB')}</strong></div></div>
          <div className="card compact"><div className="kpi"><span className="muted">Failed payments</span><strong>{summary?.failed_payments_count ?? 0}</strong></div></div>
          <div className="card compact"><div className="kpi"><span className="muted">Expired due</span><strong>{summary?.expired_due_count ?? 0}</strong></div></div>
        </div>

        {msg ? <div className="card"><p className="muted">{msg}</p></div> : null}

        <div className="card">
          <div className="row">
            <div>
              <h2>Filters</h2>
              <p className="muted">Фильтрация списка подписок.</p>
            </div>
            <div className="inline">
              <select value={status} onChange={(event) => setStatus(event.target.value)}>
                <option value="">All statuses</option>
                <option value="pending">pending</option>
                <option value="active">active</option>
                <option value="past_due">past_due</option>
                <option value="cancelled">cancelled</option>
                <option value="expired">expired</option>
              </select>
              <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="email / plan" />
              <button className="button secondary" onClick={() => void load()}>Apply</button>
            </div>
          </div>
          <div className="inline" style={{ marginTop: 12 }}>
            {statusRows.map(([key, value]) => (
              <span className={statusClass(key)} key={key}>{key}: {value}</span>
            ))}
          </div>
        </div>

        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Subscription</th>
                <th>Status</th>
                <th>Period</th>
                <th>Amount</th>
                <th>Access</th>
                <th>Ops</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6}>Loading...</td></tr>
              ) : items.length === 0 ? (
                <tr><td colSpan={6}>No subscriptions found.</td></tr>
              ) : items.map((item) => (
                <tr key={item.id}>
                  <td>
                    <strong>{item.plan?.title || item.plan_name || item.title || 'Subscription'}</strong>
                    <br /><span className="muted">{item.id}</span>
                  </td>
                  <td><span className={statusClass(item.status)}>{item.status}</span></td>
                  <td>{formatDate(item.starts_at)}<br /><span className="muted">{formatDate(item.ends_at)}</span></td>
                  <td>{formatMoney(item.amount || item.plan?.price, item.currency || item.plan?.currency || 'RUB')}</td>
                  <td>{item.entitlement_count ?? 0}</td>
                  <td>
                    <div className="inline">
                      {item.status === 'active' ? (
                        <button className="button small warning" onClick={() => void markPastDue(item.id)}>past due</button>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </ProtectedPage>
  );
}
