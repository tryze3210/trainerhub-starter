'use client';

import { useEffect, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { privateApi } from '@/lib/api';
import type { AnalyticsKpiOverview, AnalyticsRevenuePoint, AnalyticsTopTrainer, AnalyticsWarehouseHealth } from '@/types/api';

function money(value?: string | number, currency = 'RUB') {
  if (value === undefined || value === null || value === '') return `0 ${currency}`;
  return `${value} ${currency}`;
}

export default function AdminAnalyticsPage() {
  const { user } = useAuthSession();
  const isAdmin = user?.active_role === 'admin';
  const [days, setDays] = useState(30);
  const [overview, setOverview] = useState<AnalyticsKpiOverview | null>(null);
  const [series, setSeries] = useState<AnalyticsRevenuePoint[]>([]);
  const [topTrainers, setTopTrainers] = useState<AnalyticsTopTrainer[]>([]);
  const [health, setHealth] = useState<AnalyticsWarehouseHealth | null>(null);
  const [msg, setMsg] = useState('');

  async function load() {
    try {
      setMsg('');
      const [overviewPayload, seriesPayload, topPayload, healthPayload] = await Promise.all([
        privateApi.getAdminAnalyticsOverview(days),
        privateApi.getAdminAnalyticsRevenueSeries(days),
        privateApi.getAdminAnalyticsTopTrainers(days, 10),
        privateApi.getAdminAnalyticsWarehouseHealth(),
      ]);
      setOverview(overviewPayload);
      setSeries(seriesPayload);
      setTopTrainers(topPayload);
      setHealth(healthPayload);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить analytics');
    }
  }

  useEffect(() => {
    if (!isAdmin) return;
    void load();
  }, [isAdmin, days]);

  return (
    <ProtectedPage title="Admin analytics" description="KPI, revenue, trainers и health warehouse для владельца marketplace.">
      {!isAdmin ? (
        <div className="card error">У текущей сессии нет admin-role.</div>
      ) : (
        <section className="stack" style={{ gap: 24 }}>
          <div className="row" style={{ alignItems: 'flex-start' }}>
            <div className="stack" style={{ gap: 10 }}>
              <span className="badge secondary">Analytics warehouse</span>
              <h1>Marketplace analytics</h1>
              <p className="lead">Операционная аналитика: revenue, paid orders, conversion, top trainers и freshness warehouse.</p>
            </div>
            <div className="inline">
              <select className="select" value={days} onChange={(event) => setDays(Number(event.target.value))}>
                <option value={7}>7 дней</option>
                <option value={30}>30 дней</option>
                <option value={90}>90 дней</option>
                <option value={180}>180 дней</option>
              </select>
              <button className="button secondary" onClick={() => void load()}>Обновить</button>
            </div>
          </div>

          {msg ? <div className="card error">{msg}</div> : null}

          <div className="grid-4">
            <div className="card"><div className="kpi"><span className="muted">Paid revenue</span><strong>{money(overview?.revenue)}</strong></div></div>
            <div className="card"><div className="kpi"><span className="muted">Gross revenue</span><strong>{money(overview?.gross_revenue)}</strong></div></div>
            <div className="card"><div className="kpi"><span className="muted">Paid orders</span><strong>{overview?.paid_orders || 0}</strong></div></div>
            <div className="card"><div className="kpi"><span className="muted">Conversion</span><strong>{overview?.conversion_rate || '0.0000'}</strong></div></div>
          </div>

          <div className="grid-2">
            <div className="card">
              <h2 className="title-md">Revenue series</h2>
              <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                {series.length === 0 ? <p className="muted">Warehouse ещё не агрегировал revenue series.</p> : null}
                {series.slice(-14).map((point) => (
                  <div className="list-item" key={point.date}>
                    <span className="muted">{point.date}</span>
                    <strong>{money(point.paid_revenue)} · paid orders {point.paid_orders}</strong>
                    <small>gross {money(point.gross_revenue)} · total orders {point.total_orders}</small>
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <h2 className="title-md">Top trainers</h2>
              <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                {topTrainers.length === 0 ? <p className="muted">Top trainers пока пустой.</p> : null}
                {topTrainers.map((trainer) => (
                  <div className="list-item" key={trainer.trainer_id}>
                    <span className="muted">{trainer.trainer_id}</span>
                    <strong>{money(trainer.paid_revenue)} · orders {trainer.paid_orders}</strong>
                    <small>active subscribers {trainer.active_subscribers} · new customers {trainer.new_customers}</small>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="card">
            <div className="row">
              <div>
                <h2 className="title-md">Warehouse health</h2>
                <p className="muted">Последняя успешная агрегация и возможная ошибка.</p>
              </div>
              <span className={`badge ${health?.status === 'healthy' ? 'success' : 'warning'}`}>{health?.status || 'empty'}</span>
            </div>
            <div className="grid-4" style={{ marginTop: 16 }}>
              <div className="list-item"><span className="muted">Rows written</span><strong>{health?.last_success_rows_written || 0}</strong></div>
              <div className="list-item"><span className="muted">Range start</span><strong>{health?.last_success_range_start || '—'}</strong></div>
              <div className="list-item"><span className="muted">Range end</span><strong>{health?.last_success_range_end || '—'}</strong></div>
              <div className="list-item"><span className="muted">Failure</span><strong>{health?.latest_failure_message || '—'}</strong></div>
            </div>
          </div>
        </section>
      )}
    </ProtectedPage>
  );
}
