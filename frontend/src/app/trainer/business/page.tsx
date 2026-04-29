'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { trainersApi } from '@/lib/api';
import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import type { TrainerBusinessDashboard } from '@/types/api';

function formatMoney(value?: string | number, currency = 'RUB') {
  if (value === undefined || value === null || value === '') return `0.00 ${currency}`;
  return `${value} ${currency}`;
}

function statusBadge(status?: string) {
  if (!status) return 'badge secondary';
  if (['ready', 'done', 'approved', 'paid', 'healthy'].includes(status)) return 'badge success';
  if (['blocked', 'blocker', 'critical', 'rejected'].includes(status)) return 'badge error';
  return 'badge warning';
}

export default function TrainerBusinessPage() {
  const [days, setDays] = useState(30);
  const [dashboard, setDashboard] = useState<TrainerBusinessDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        setLoading(true);
        setError('');
        const payload = await trainersApi.getTrainerBusinessDashboard(days);
        if (!cancelled) setDashboard(payload);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Не удалось загрузить business dashboard');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [days]);

  const currency = dashboard?.payouts.balance.currency || 'RUB';
  const latestRevenue = useMemo(() => {
    return (dashboard?.commerce.revenue_series || []).slice(-10);
  }, [dashboard]);

  return (
    <ProtectedPage title="Trainer business" description="Бизнес-кабинет тренера доступен только после авторизации.">
      <TrainerDashboardShell
        title="Trainer business cockpit"
        description="Продажи, выручка, payout readiness, контент, модерация и операционная готовность тренера в одном месте."
      >
        <div className="row" style={{ justifyContent: 'space-between', gap: 12 }}>
          <div className="stack" style={{ gap: 4 }}>
            <span className={statusBadge(dashboard?.readiness.status)}>{dashboard?.readiness.status || 'loading'}</span>
            <p className="muted" style={{ margin: 0 }}>Период аналитики: последние {days} дней</p>
          </div>
          <div className="row" style={{ gap: 8 }}>
            {[7, 30, 90].map((value) => (
              <button
                key={value}
                type="button"
                className={`button ${days === value ? 'primary' : 'secondary'}`}
                onClick={() => setDays(value)}
              >
                {value}d
              </button>
            ))}
          </div>
        </div>

        {loading ? <div className="card"><p className="muted">Загружаем бизнес-метрики…</p></div> : null}
        {error ? <div className="card error">{error}</div> : null}

        {dashboard ? (
          <>
            <div className="grid-4">
              <div className="card"><div className="kpi"><span className="muted">Выручка периода</span><strong>{formatMoney(dashboard.commerce.revenue_period, currency)}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Заказы периода</span><strong>{dashboard.commerce.period_orders_count}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Покупатели</span><strong>{dashboard.commerce.customers_count}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Средний чек</span><strong>{formatMoney(dashboard.commerce.avg_order_value, currency)}</strong></div></div>
            </div>

            <div className="grid-4">
              <div className="card"><div className="kpi"><span className="muted">Available payout</span><strong>{formatMoney(dashboard.payouts.balance.available_amount, currency)}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Reserved payout</span><strong>{formatMoney(dashboard.payouts.balance.reserved_amount, currency)}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Lifetime earned</span><strong>{formatMoney(dashboard.payouts.balance.lifetime_earned_amount, currency)}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Active payouts</span><strong>{dashboard.payouts.active_requests_count}</strong></div></div>
            </div>

            <div className="grid-2">
              <div className="card">
                <div className="row" style={{ justifyContent: 'space-between', gap: 12 }}>
                  <h2 className="title-md" style={{ margin: 0 }}>Business readiness</h2>
                  <span className={statusBadge(dashboard.readiness.status)}>{dashboard.readiness.status}</span>
                </div>
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {dashboard.readiness.checks.map((check) => (
                    <div className="list-item" key={check.code}>
                      <span>{check.title}</span>
                      <span className={statusBadge(check.status)}>{check.status}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="card">
                <div className="row" style={{ justifyContent: 'space-between', gap: 12 }}>
                  <h2 className="title-md" style={{ margin: 0 }}>Content inventory</h2>
                  <Link className="button secondary" href="/trainer/videos">Content studio</Link>
                </div>
                <div className="grid-2" style={{ marginTop: 16 }}>
                  <div className="card compact"><div className="kpi"><span className="muted">Drafts</span><strong>{dashboard.content.drafts.total}</strong></div></div>
                  <div className="card compact"><div className="kpi"><span className="muted">Published</span><strong>{dashboard.content.published.total}</strong></div></div>
                  <div className="card compact"><div className="kpi"><span className="muted">Pending review</span><strong>{dashboard.content.pending_review_count}</strong></div></div>
                  <div className="card compact"><div className="kpi"><span className="muted">Order items</span><strong>{dashboard.commerce.order_items_count}</strong></div></div>
                </div>
              </div>
            </div>

            <div className="grid-2">
              <div className="card">
                <h2 className="title-md">Revenue trend</h2>
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {latestRevenue.length === 0 ? (
                    <p className="muted">Пока нет оплаченных заказов за выбранный период.</p>
                  ) : (
                    latestRevenue.map((point) => (
                      <div className="list-item" key={point.date}>
                        <span className="muted">{point.date}</span>
                        <strong>{formatMoney(point.revenue, currency)}</strong>
                        <small>orders {point.orders_count}</small>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="card">
                <h2 className="title-md">Top products</h2>
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {dashboard.commerce.top_products.length === 0 ? (
                    <p className="muted">Пока нет продаж по продуктам.</p>
                  ) : (
                    dashboard.commerce.top_products.map((item) => (
                      <div className="list-item" key={`${item.item_type}-${item.title}`}>
                        <div className="stack" style={{ gap: 2 }}>
                          <strong>{item.title}</strong>
                          <small>{item.item_type} · {item.orders_count} orders</small>
                        </div>
                        <strong>{formatMoney(item.revenue, currency)}</strong>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            <div className="grid-2">
              <div className="card">
                <div className="row" style={{ justifyContent: 'space-between', gap: 12 }}>
                  <h2 className="title-md" style={{ margin: 0 }}>Latest payout requests</h2>
                  <Link className="button secondary" href="/payouts">Все выплаты</Link>
                </div>
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {dashboard.payouts.latest_requests.length === 0 ? (
                    <p className="muted">Заявок на выплаты пока нет.</p>
                  ) : (
                    dashboard.payouts.latest_requests.map((payout) => (
                      <div className="list-item" key={payout.id}>
                        <div className="stack" style={{ gap: 2 }}>
                          <strong>{formatMoney(payout.amount, payout.currency)}</strong>
                          <small>{payout.destination_masked || 'destination not set'}</small>
                        </div>
                        <span className={statusBadge(payout.status)}>{payout.status}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="card">
                <h2 className="title-md">Moderation & risk</h2>
                <div className="grid-2" style={{ marginTop: 16 }}>
                  <div className="card compact"><div className="kpi"><span className="muted">Open cases</span><strong>{dashboard.moderation.open_cases_count}</strong></div></div>
                  <div className="card compact"><div className="kpi"><span className="muted">Risk flags</span><strong>{dashboard.moderation.risk_flags_count}</strong></div></div>
                </div>
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {dashboard.moderation.latest_cases.length === 0 ? (
                    <p className="muted">Нет открытых moderation cases.</p>
                  ) : (
                    dashboard.moderation.latest_cases.map((item) => (
                      <div className="list-item" key={String(item.id)}>
                        <span>{String(item.title || 'Moderation case')}</span>
                        <span className={statusBadge(String(item.status || ''))}>{String(item.status || 'unknown')}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </>
        ) : null}
      </TrainerDashboardShell>
    </ProtectedPage>
  );
}
