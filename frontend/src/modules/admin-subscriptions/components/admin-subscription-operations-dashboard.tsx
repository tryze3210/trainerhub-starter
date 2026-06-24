'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuthSession } from '@/components/auth-provider';
import {
  adminSubscriptionsApi,
  type AdminSubscriptionItem,
  type AdminSubscriptionOverview,
  type SubscriptionLifecyclePolicy,
  type SubscriptionLifecycleSummary,
  type SubscriptionStatus,
} from '@/modules/admin-subscriptions/api';

const STATUS_OPTIONS = ['', 'trial', 'pending', 'active', 'past_due', 'cancelled', 'expired'];

function formatDate(value?: string | null): string {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function money(value?: string | number | null, currency = 'RUB'): string {
  if (value === undefined || value === null || value === '') return `0 ${currency}`;
  return `${value} ${currency}`;
}

function statusClass(status?: SubscriptionStatus): string {
  if (status === 'trial') return 'success';
  if (status === 'active') return 'success';
  if (status === 'past_due') return 'warning';
  if (status === 'cancelled' || status === 'expired') return 'secondary';
  return 'secondary';
}

function getSummaryNumber(overview: AdminSubscriptionOverview | null, key: string): number {
  const value = overview?.summary?.[key];
  return typeof value === 'number' ? value : Number(value || 0);
}

function getPlanTitle(item: AdminSubscriptionItem): string {
  return item.plan?.title || item.plan_name || item.title || 'Subscription plan';
}

function getPeriodEnd(item: AdminSubscriptionItem): string | null | undefined {
  return item.current_period_end || item.ends_at;
}

export function AdminSubscriptionOperationsDashboard() {
  const { user } = useAuthSession();
  const isAdmin = user?.active_role === 'admin';

  const [items, setItems] = useState<AdminSubscriptionItem[]>([]);
  const [overview, setOverview] = useState<AdminSubscriptionOverview | null>(null);
  const [policy, setPolicy] = useState<SubscriptionLifecyclePolicy | null>(null);
  const [summary, setSummary] = useState<SubscriptionLifecycleSummary | null>(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');
  const [days, setDays] = useState(30);
  const [reason, setReason] = useState('manual_admin_subscription_ops');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [busyOperation, setBusyOperation] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!isAdmin) return;
    try {
      setLoading(true);
      setMessage('');
      const [overviewPayload, itemsPayload, policyPayload, summaryPayload] = await Promise.all([
        adminSubscriptionsApi.getOverview(days),
        adminSubscriptionsApi.listItems({ status: statusFilter || undefined, search: search || undefined, limit: 100 }),
        adminSubscriptionsApi.getLifecyclePolicy(),
        adminSubscriptionsApi.getLifecycleSummary(days),
      ]);
      setOverview(overviewPayload);
      setItems(itemsPayload);
      setPolicy(policyPayload);
      setSummary(summaryPayload);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Не удалось загрузить subscription operations.');
    } finally {
      setLoading(false);
    }
  }, [days, isAdmin, search, statusFilter]);

  useEffect(() => {
    void load();
  }, [load]);

  const computed = useMemo(() => {
    return {
      total: getSummaryNumber(overview, 'total_count') || items.length,
      trial: getSummaryNumber(overview, 'trial_count') || items.filter((item) => item.status === 'trial').length,
      active: getSummaryNumber(overview, 'active_count') || items.filter((item) => item.status === 'active').length,
      pastDue: getSummaryNumber(overview, 'past_due_count') || items.filter((item) => item.status === 'past_due').length,
      cancelled: getSummaryNumber(overview, 'cancelled_count') || items.filter((item) => item.status === 'cancelled').length,
      expired: getSummaryNumber(overview, 'expired_count') || items.filter((item) => item.status === 'expired').length,
      revenue: overview?.summary?.subscription_revenue,
      mrr: overview?.summary?.estimated_mrr,
      currency: String(overview?.summary?.currency || 'RUB'),
    };
  }, [items, overview]);

  async function runAction(operation: string, action: () => Promise<unknown>, successMessage: string) {
    try {
      setBusyOperation(operation);
      setMessage('');
      await action();
      setMessage(successMessage);
      await load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Операция не выполнена.');
    } finally {
      setBusyOperation(null);
    }
  }

  if (!isAdmin) {
    return (
      <section className="page-shell stack">
        <div className="card empty-state">
          <span className="eyebrow">Admin only</span>
          <h1>Операции подписок недоступны</h1>
          <p>Для управления subscription lifecycle нужна admin-role.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="page-shell stack">
      <section className="hero card stack">
        <span className="eyebrow">Subscription operations</span>
        <div className="row">
          <div>
            <h1>Операции подписок</h1>
            <p>
              Lifecycle overview, фильтры по статусам, mark-past-due, expire-due, sync-entitlements и
              reconciliation для recurring revenue.
            </p>
          </div>
          <div className="inline" style={{ flexWrap: 'wrap' }}>
            <button className="button secondary" disabled={loading} onClick={() => void load()}>
              Обновить
            </button>
            <Link className="button ghost" href="/admin/operations">
              Operations hub
            </Link>
          </div>
        </div>
        {message ? <div className="card compact">{message}</div> : null}
      </section>

      <section className="grid-4">
        <div className="card stat-card">
          <span className="muted">Всего</span>
          <strong>{computed.total}</strong>
          <small>trial: {computed.trial}</small>
        </div>
        <div className="card stat-card">
          <span className="muted">Active</span>
          <strong>{computed.active}</strong>
          <small>доступ должен быть активен</small>
        </div>
        <div className="card stat-card">
          <span className="muted">Past due</span>
          <strong>{computed.pastDue}</strong>
          <small>требуют внимания</small>
        </div>
        <div className="card stat-card">
          <span className="muted">MRR estimate</span>
          <strong>{money(computed.mrr as string | number | undefined, computed.currency)}</strong>
          <small>revenue: {money(computed.revenue as string | number | undefined, computed.currency)}</small>
        </div>
      </section>

      <section className="grid-2">
        <div className="card stack">
          <div className="row">
            <div>
              <h3>Фильтры</h3>
              <p className="muted">Фокусируй очередь по статусу, пользователю, плану или id.</p>
            </div>
          </div>
          <div className="grid-3">
            <label className="stack compact">
              <span className="muted">Статус</span>
              <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                {STATUS_OPTIONS.map((status) => (
                  <option key={status || 'all'} value={status}>
                    {status || 'all'}
                  </option>
                ))}
              </select>
            </label>
            <label className="stack compact">
              <span className="muted">Search</span>
              <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="user / plan / id" />
            </label>
            <label className="stack compact">
              <span className="muted">Период</span>
              <select value={days} onChange={(event) => setDays(Number(event.target.value))}>
                {[7, 30, 90, 180, 365].map((value) => (
                  <option key={value} value={value}>
                    {value} дней
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>

        <div className="card stack">
          <h3>Lifecycle control</h3>
          <p className="muted">
            Admin actions используют backend lifecycle policy и audit trail. Reconcile сначала запускай dry-run.
          </p>
          <label className="stack compact">
            <span className="muted">Reason / audit note</span>
            <input value={reason} onChange={(event) => setReason(event.target.value)} placeholder="ops reason" />
          </label>
          <div className="inline" style={{ flexWrap: 'wrap' }}>
            <button
              className="button secondary"
              disabled={!!busyOperation}
              onClick={() =>
                void runAction(
                  'expire-due',
                  () => adminSubscriptionsApi.expireDue(reason),
                  'Expire-due command выполнена.',
                )
              }
            >
              Expire due
            </button>
            <button
              className="button secondary"
              disabled={!!busyOperation}
              onClick={() =>
                void runAction(
                  'reconcile-dry',
                  () => adminSubscriptionsApi.reconcileEntitlements(true),
                  'Entitlement reconciliation dry-run выполнен.',
                )
              }
            >
              Reconcile dry-run
            </button>
            <button
              className="button"
              disabled={!!busyOperation}
              onClick={() =>
                void runAction(
                  'reconcile-apply',
                  () => adminSubscriptionsApi.reconcileEntitlements(false),
                  'Entitlement reconciliation применён.',
                )
              }
            >
              Apply reconciliation
            </button>
          </div>
        </div>
      </section>

      <section className="grid-2">
        <div className="card stack">
          <h3>Lifecycle policy</h3>
          {policy?.statuses?.length ? (
            <div className="stack compact">
              {policy.statuses.slice(0, 8).map((status) => (
                <div className="list-item" key={status.code}>
                  <span className={`badge ${statusClass(status.code)}`}>{status.code}</span>
                  <strong>{status.label || status.code}</strong>
                  <small>{status.description || (status.terminal ? 'terminal' : 'non-terminal')}</small>
                </div>
              ))}
            </div>
          ) : (
            <p className="muted">Policy endpoint доступен после v8.46 lifecycle hardening.</p>
          )}
        </div>

        <div className="card stack">
          <h3>Lifecycle issues</h3>
          {summary?.issues?.length ? (
            <div className="stack compact">
              {summary.issues.slice(0, 8).map((issue) => (
                <div className="list-item" key={`${issue.code}-${issue.severity || 'issue'}`}>
                  <span className="badge warning">{issue.severity || 'warning'}</span>
                  <strong>{issue.code}</strong>
                  <small>{issue.message || `${issue.count || 0} affected`}</small>
                </div>
              ))}
            </div>
          ) : (
            <p className="muted">Активных lifecycle issues нет.</p>
          )}
        </div>
      </section>

      <section className="card stack">
        <div className="row">
          <div>
            <h3>Subscription queue</h3>
            <p className="muted">{loading ? 'Загрузка…' : `Найдено: ${items.length}`}</p>
          </div>
        </div>

        {items.length === 0 && !loading ? (
          <div className="empty-state">
            <h3>Очередь пуста</h3>
            <p>Подписок под выбранные фильтры нет.</p>
          </div>
        ) : null}

        <div className="grid-2">
          {items.map((item) => (
            <article className="card compact stack" key={item.id}>
              <div className="row">
                <div>
                  <span className="eyebrow">{getPlanTitle(item)}</span>
                  <h3>{money(item.amount || item.price_amount || item.plan?.price, item.currency || item.plan?.currency || 'RUB')}</h3>
                </div>
                <span className={`badge ${statusClass(item.status)}`}>{item.status || 'unknown'}</span>
              </div>

              <div className="grid-3">
                <div className="list-item">
                  <span className="muted">User</span>
                  <strong>{item.user_id || item.customer_id || '—'}</strong>
                </div>
                <div className="list-item">
                  <span className="muted">Period end</span>
                  <strong>{formatDate(getPeriodEnd(item))}</strong>
                </div>
                <div className="list-item">
                  <span className="muted">Entitlements</span>
                  <strong>{item.entitlement_count ?? '—'}</strong>
                </div>
              </div>

              <div className="inline" style={{ flexWrap: 'wrap' }}>
                <button
                  className="button secondary"
                  disabled={!!busyOperation || item.status === 'past_due'}
                  onClick={() =>
                    void runAction(
                      `past-due-${item.id}`,
                      () => adminSubscriptionsApi.markPastDue(item.id, reason),
                      'Подписка переведена в past_due.',
                    )
                  }
                >
                  Mark past due
                </button>
                <button
                  className="button secondary"
                  disabled={!!busyOperation}
                  onClick={() =>
                    void runAction(
                      `sync-${item.id}`,
                      () => adminSubscriptionsApi.syncEntitlements(item.id, reason),
                      'Entitlements синхронизированы.',
                    )
                  }
                >
                  Sync access
                </button>
                <Link className="button ghost" href={`/admin/subscriptions/${item.id}`}>
                  Detail
                </Link>
              </div>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}
