'use client';

import { useEffect, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { isAdminUser } from '@/lib/authz';
import { privateApi } from '@/lib/api';
import type { AnalyticsKpiOverview, AnalyticsRevenuePoint, AnalyticsTopTrainer, AnalyticsWarehouseHealth } from '@/types/api';

function money(value?: string | number, currency = 'RUB') {
  if (value === undefined || value === null || value === '') return `0 ${currency}`;
  return `${value} ${currency}`;
}

export default function AdminАналитикаPage() {
  const { user } = useAuthSession();
  const isAdmin = isAdminUser(user);
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
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить аналитику');
    }
  }

  useEffect(() => {
    if (!isAdmin) return;
    void load();
  }, [isAdmin, days]);

  return (
    <ProtectedPage title="Аналитика администратора" description="KPI, выручка, тренеры и состояние витрины данных для владельца маркетплейса.">
      {!isAdmin ? (
        <div className="card error">У текущей сессии нет роли администратора.</div>
      ) : (
        <section className="stack" style={{ gap: 24 }}>
          <div className="row" style={{ alignItems: 'flex-start' }}>
            <div className="stack" style={{ gap: 10 }}>
              <span className="badge secondary">Аналитика витрины данных</span>
              <h1>Аналитика маркетплейса</h1>
              <p className="lead">Операционная аналитика: выручка, оплаченные заказы, конверсия, топ тренеров и актуальность витрины данных.</p>
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
            <div className="card"><div className="kpi"><span className="muted">Оплаченная выручка</span><strong>{money(overview?.revenue)}</strong></div></div>
            <div className="card"><div className="kpi"><span className="muted">Валовая выручка</span><strong>{money(overview?.gross_revenue)}</strong></div></div>
            <div className="card"><div className="kpi"><span className="muted">Оплаченные заказы</span><strong>{overview?.paid_orders || 0}</strong></div></div>
            <div className="card"><div className="kpi"><span className="muted">Конверсия</span><strong>{overview?.conversion_rate || '0.0000'}</strong></div></div>
          </div>

          <div className="grid-2">
            <div className="card">
              <h2 className="title-md">Динамика выручки</h2>
              <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                {series.length === 0 ? <p className="muted">Витрина данных ещё не агрегировала динамику выручки.</p> : null}
                {series.slice(-14).map((point) => (
                  <div className="list-item" key={point.date}>
                    <span className="muted">{point.date}</span>
                    <strong>{money(point.paid_revenue)} · оплаченных заказов {point.paid_orders}</strong>
                    <small>валовая выручка {money(point.gross_revenue)} · всего заказов {point.total_orders}</small>
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <h2 className="title-md">Топ тренеров</h2>
              <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                {topTrainers.length === 0 ? <p className="muted">Топ тренеров пока пустой.</p> : null}
                {topTrainers.map((trainer) => (
                  <div className="list-item" key={trainer.trainer_id}>
                    <span className="muted">{trainer.trainer_id}</span>
                    <strong>{money(trainer.paid_revenue)} · заказов {trainer.paid_orders}</strong>
                    <small>активных подписчиков {trainer.active_subscribers} · новых клиентов {trainer.new_customers}</small>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="card">
            <div className="row">
              <div>
                <h2 className="title-md">Состояние витрины данных</h2>
                <p className="muted">Последняя успешная агрегация и возможная ошибка.</p>
              </div>
              <span className={`badge ${health?.status === 'healthy' ? 'success' : 'warning'}`}>{health?.status || 'empty'}</span>
            </div>
            <div className="grid-4" style={{ marginTop: 16 }}>
              <div className="list-item"><span className="muted">Записано строк</span><strong>{health?.last_success_rows_written || 0}</strong></div>
              <div className="list-item"><span className="muted">Начало периода</span><strong>{health?.last_success_range_start || '—'}</strong></div>
              <div className="list-item"><span className="muted">Конец периода</span><strong>{health?.last_success_range_end || '—'}</strong></div>
              <div className="list-item"><span className="muted">Ошибка</span><strong>{health?.latest_failure_message || '—'}</strong></div>
            </div>
          </div>
        </section>
      )}
    </ProtectedPage>
  );
}
