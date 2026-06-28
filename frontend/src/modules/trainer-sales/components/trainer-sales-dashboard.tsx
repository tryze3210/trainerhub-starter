'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { trainerSalesApi, type TrainerSalesDashboardSnapshot } from '@/modules/trainer-sales/api';
import type { TrainerContentPerformanceRow, TrainerSaleAnalyticsRow } from '@/modules/trainer-analytics/api';
import type { TrainerRevenueTransaction } from '@/modules/trainer-revenue/api';

const DAY_OPTIONS = [7, 30, 90, 365];

function money(value?: string | number | null, currency = 'RUB') {
  const amount = Number(value ?? 0);
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
  }).format(Number.isFinite(amount) ? amount : 0);
}

function dateTime(value?: string | null) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function statusText(value?: string | null) {
  return value ? value.replaceAll('_', ' ') : '-';
}

function percent(value?: string | number | null) {
  const parsed = Number(value ?? 0);
  if (!Number.isFinite(parsed)) return '0%';
  return `${parsed.toFixed(2)}%`;
}

function shortId(value?: string | null) {
  if (!value) return '-';
  return value.length > 14 ? `${value.slice(0, 8)}...${value.slice(-4)}` : value;
}

function isRefundTransaction(entry: TrainerRevenueTransaction) {
  const text = `${entry.entry_type} ${entry.source_type} ${entry.description}`.toLowerCase();
  return text.includes('refund') || entry.direction === 'debit';
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

function ContentPerformanceTable({ rows, currency }: { rows: TrainerContentPerformanceRow[]; currency: string }) {
  if (!rows.length) return <p className="muted">Контентных продаж за период пока нет.</p>;

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>Контент</th>
            <th>Просмотры</th>
            <th>Покупки</th>
            <th>Конверсия</th>
            <th>Чистая выручка</th>
            <th>Возвраты</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((item) => (
            <tr key={`${item.content_type}:${item.id}`}>
              <td>
                <div className="stack" style={{ gap: 4 }}>
                  <strong>{item.title}</strong>
                  <span className="muted">{item.content_type} · {item.status}</span>
                </div>
              </td>
              <td>{item.views_count}</td>
              <td>{item.purchase_count}</td>
              <td>{percent(item.conversion_rate)}</td>
              <td>{money(item.net_revenue, item.currency || currency)}</td>
              <td>{money(item.refund_amount, item.currency || currency)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SalesTable({ rows, currency }: { rows: TrainerSaleAnalyticsRow[]; currency: string }) {
  if (!rows.length) return <p className="muted">Продаж за период пока нет.</p>;

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>Заказ</th>
            <th>Продукт</th>
            <th>Кол-во</th>
            <th>Сумма</th>
            <th>Статус</th>
            <th>Дата</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((sale) => (
            <tr key={`${sale.order_id}:${sale.item_type}:${sale.item_id}`}>
              <td>{shortId(sale.order_id)}</td>
              <td>
                <div className="stack" style={{ gap: 4 }}>
                  <strong>{sale.title}</strong>
                  <span className="muted">{sale.item_type} · {shortId(sale.item_id)}</span>
                </div>
              </td>
              <td>{sale.quantity}</td>
              <td>{money(sale.total_price, sale.currency || currency)}</td>
              <td><span className="badge secondary">{statusText(sale.order_status)}</span></td>
              <td>{dateTime(sale.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RefundTable({ rows, currency }: { rows: TrainerRevenueTransaction[]; currency: string }) {
  if (!rows.length) return <p className="muted">Операций возврата за период не найдено.</p>;

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>Дата</th>
            <th>Тип</th>
            <th>Сумма</th>
            <th>Статус</th>
            <th>Источник</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((entry) => (
            <tr key={entry.id}>
              <td>{dateTime(entry.created_at)}</td>
              <td>{statusText(entry.entry_type)}</td>
              <td>{money(entry.amount, entry.currency || currency)}</td>
              <td><span className="badge secondary">{statusText(entry.status)}</span></td>
              <td>{entry.source_type}:{shortId(entry.source_id)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function StudentAccessTable({ rows, salesByContent }: { rows: TrainerContentPerformanceRow[]; salesByContent: Record<string, number> }) {
  if (!rows.length) return <p className="muted">Доступов учеников пока нет.</p>;

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>Контент</th>
            <th>Тип</th>
            <th>Доступы учеников</th>
            <th>Статус</th>
            <th>Обновлено</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((item) => {
            const salesCount = salesByContent[item.id] ?? item.purchase_count;
            return (
              <tr key={`access:${item.content_type}:${item.id}`}>
                <td>{item.title}</td>
                <td>{item.content_type}</td>
                <td>{salesCount}</td>
                <td><span className="badge secondary">{salesCount > 0 ? 'доступ выдан' : 'нет активных покупателей'}</span></td>
                <td>{dateTime(item.updated_at)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function TrainerSalesDashboard() {
  const [days, setDays] = useState(30);
  const [state, setState] = useState<TrainerSalesDashboardSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  async function load(selectedDays = days) {
    try {
      setLoading(true);
      setMessage('');
      setState(await trainerSalesApi.getSnapshot(selectedDays, 50));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Не удалось загрузить панель продаж');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load(days);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days]);

  const currency = state?.overview.currency || state?.revenue.currency || 'RUB';
  const refundTransactions = useMemo(
    () => (state?.transactions.results || []).filter(isRefundTransaction),
    [state?.transactions.results]
  );
  const конверсияRate = useMemo(() => {
    const просмотров = state?.overview.performance.total_views || 0;
    const purchases = state?.overview.performance.total_purchases || 0;
    return просмотров ? (purchases / просмотров) * 100 : 0;
  }, [state]);
  const salesByContent = useMemo(() => {
    return (state?.sales.results || []).reduce<Record<string, number>>((acc, sale) => {
      acc[sale.matched_content_id] = (acc[sale.matched_content_id] || 0) + sale.quantity;
      return acc;
    }, {});
  }, [state?.sales.results]);

  return (
    <section className="trainer-sales-page stack" style={{ gap: 24 }}>
      <div className="card row" style={{ gap: 16, alignItems: 'flex-end' }}>
        <div className="stack" style={{ gap: 8 }}>
          <span className="badge secondary">Продажи</span>
          <h2 className="title-md">Продажи тренера</h2>
          <p className="muted">Продажи, выручка, возвраты, конверсия и выданные доступы учеников.</p>
        </div>
        <div className="inline" style={{ gap: 10, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
          <select value={days} onChange={(event) => setDays(Number(event.target.value))} className="input" aria-label="Период продаж">
            {DAY_OPTIONS.map((option) => (
              <option key={option} value={option}>{option} дней</option>
            ))}
          </select>
          <button type="button" className="button secondary" onClick={() => void load()} disabled={loading}>
            {loading ? 'Загрузка...' : 'Обновить'}
          </button>
          <Link href="/trainer/dashboard/revenue" className="button ghost">Детализация выручки</Link>
        </div>
      </div>

      {message ? <div className="card error">{message}</div> : null}
      {loading && !state ? <div className="card">Загрузка панели продаж...</div> : null}

      {state ? (
        <>
          <div className="grid-4">
            <StatCard title="Продажи" value={state.sales.summary.purchased_units} hint={`${state.sales.summary.matched_sales} заказов`} />
            <StatCard title="Чистая выручка" value={money(state.revenue.revenue.net_revenue, currency)} hint={`${days} дней`} />
            <StatCard title="Возвраты" value={money(state.revenue.revenue.refunds, currency)} hint={`${refundTransactions.length} операций`} />
            <StatCard title="Конверсия" value={percent(конверсияRate)} hint={`${state.overview.performance.total_views} просмотров`} />
          </div>

          <div className="grid-4">
            <StatCard title="Валовые продажи" value={money(state.overview.sales.gross_order_sales, currency)} />
            <StatCard title="Покупки контента" value={state.overview.performance.total_purchases} />
            <StatCard title="Активный каталог" value={state.overview.counts.published_products + state.overview.counts.published_videos} />
            <StatCard title="Доступно к выплате" value={money(state.revenue.revenue.available_payout, currency)} />
          </div>

          <div className="trainer-sales-table-card">
            <div className="stack" style={{ gap: 8, marginBottom: 18 }}>
              <span className="badge secondary">Лучшие продукты</span>
              <h2 className="title-md">Выручка и конверсия</h2>
            </div>
            <ContentPerformanceTable rows={state.content.results} currency={currency} />
          </div>

          <div className="trainer-sales-table-card">
            <div className="stack" style={{ gap: 8, marginBottom: 18 }}>
              <span className="badge secondary">Продажи</span>
              <h2 className="title-md">Последние продажи</h2>
            </div>
            <SalesTable rows={state.sales.results} currency={currency} />
          </div>

          <div className="grid-2">
            <div className="trainer-sales-card">
              <div className="stack" style={{ gap: 8, marginBottom: 18 }}>
                <span className="badge secondary">Возвраты</span>
                <h2 className="title-md">Возвраты</h2>
              </div>
              <RefundTable rows={refundTransactions} currency={currency} />
            </div>

            <div className="trainer-sales-card">
              <div className="stack" style={{ gap: 8, marginBottom: 18 }}>
                <span className="badge secondary">Доступы учеников</span>
                <h2 className="title-md">Доступы учеников</h2>
              </div>
              <StudentAccessTable rows={state.content.results} salesByContent={salesByContent} />
            </div>
          </div>
        </>
      ) : null}
    </section>
  );
}
