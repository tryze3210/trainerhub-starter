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
  if (!value) return 'Дата не указана';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function percent(value?: string | number | null) {
  const parsed = Number(value ?? 0);
  if (!Number.isFinite(parsed)) return '0%';
  return `${parsed.toFixed(1)}%`;
}

function contentTypeLabel(value?: string | null) {
  if (value === 'video') return 'Видео';
  if (value === 'product') return 'Продукт';
  if (value === 'subscription') return 'Подписка';
  return 'Материал';
}

function saleStatusLabel(value?: string | null) {
  const status = (value || '').toLowerCase();
  if (status === 'paid' || status === 'completed' || status === 'succeeded') return 'Оплачено';
  if (status === 'pending') return 'Ожидает';
  if (status === 'refunded') return 'Возврат выполнен';
  if (status === 'disputed' || status === 'chargeback') return 'Спор';
  if (status === 'failed' || status === 'error') return 'Ошибка';
  if (status === 'cancelled') return 'Отменено';
  return 'Требуется проверка';
}

function statusTone(value?: string | null) {
  const status = (value || '').toLowerCase();
  if (['paid', 'completed', 'succeeded', 'published', 'active'].includes(status)) return 'success';
  if (['pending', 'review', 'submitted', 'under_review'].includes(status)) return 'warning';
  if (['failed', 'error', 'cancelled', 'refunded', 'disputed', 'chargeback'].includes(status)) return 'danger';
  return 'neutral';
}

function statusClass(value?: string | null) {
  return `trainer-finance-status trainer-finance-status-${statusTone(value)}`;
}

function isRefundTransaction(entry: TrainerRevenueTransaction) {
  const text = `${entry.entry_type} ${entry.source_type} ${entry.description}`.toLowerCase();
  return text.includes('refund') || text.includes('chargeback') || entry.direction === 'debit';
}

function KpiCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <article className="trainer-finance-kpi-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {hint ? <small>{hint}</small> : null}
    </article>
  );
}

function ProductRail({ rows, currency }: { rows: TrainerContentPerformanceRow[]; currency: string }) {
  if (!rows.length) {
    return (
      <div className="trainer-finance-empty">
        <strong>Продуктов с продажами пока нет</strong>
        <p>Когда ученик купит видео или продукт, лучшие позиции появятся в этой ленте.</p>
      </div>
    );
  }

  return (
    <div className="trainer-sales-rail" aria-label="Лучшие продукты">
      {rows.slice(0, 12).map((item) => (
        <article className="trainer-sales-product-card" key={`${item.content_type}:${item.id}`}>
          <span className={statusClass(item.status)}>{saleStatusLabel(item.status)}</span>
          <strong>{item.title}</strong>
          <span>{contentTypeLabel(item.content_type)} · {item.purchase_count} продаж</span>
          <span>{money(item.net_revenue, item.currency || currency)}</span>
          <small>Возвраты: {money(item.refund_amount, item.currency || currency)} · конверсия {percent(item.conversion_rate)}</small>
        </article>
      ))}
    </div>
  );
}

function SalesTimeline({ rows, currency }: { rows: TrainerSaleAnalyticsRow[]; currency: string }) {
  if (!rows.length) {
    return (
      <div className="trainer-finance-empty">
        <strong>Продаж за период пока нет</strong>
        <p>Проверьте период или откройте каталог, чтобы убедиться, что продукты опубликованы.</p>
      </div>
    );
  }

  return (
    <div className="trainer-finance-timeline">
      {rows.slice(0, 12).map((sale) => (
        <article className="trainer-sales-timeline-card" key={`${sale.order_id}:${sale.item_type}:${sale.item_id}`}>
          <div className="trainer-finance-row">
            <div>
              <strong>{sale.title}</strong>
              <span className="trainer-finance-muted">{contentTypeLabel(sale.matched_content_type)} · {dateTime(sale.created_at)}</span>
            </div>
            <span className={statusClass(sale.order_status)}>{saleStatusLabel(sale.order_status)}</span>
          </div>
          <div className="trainer-finance-row">
            <span>Покупатель</span>
            <strong>{sale.quantity} шт. · {money(sale.total_price, sale.currency || currency)}</strong>
          </div>
        </article>
      ))}
    </div>
  );
}

function RefundPanel({ rows, currency }: { rows: TrainerRevenueTransaction[]; currency: string }) {
  if (!rows.length) {
    return (
      <div className="trainer-finance-empty">
        <strong>Рисков не найдено</strong>
        <p>За выбранный период нет возвратов, спорных операций или ошибок списания.</p>
      </div>
    );
  }

  return (
    <div className="trainer-finance-timeline">
      {rows.slice(0, 8).map((entry) => (
        <article className="trainer-finance-compact-card" key={entry.id}>
          <div className="trainer-finance-row">
            <strong>{money(entry.amount, entry.currency || currency)}</strong>
            <span className={statusClass(entry.status)}>{saleStatusLabel(entry.status)}</span>
          </div>
          <span>{dateTime(entry.created_at)}</span>
          <small className="trainer-finance-muted">{entry.description || 'Финансовая операция'}</small>
        </article>
      ))}
    </div>
  );
}

function AccessPanel({ rows, salesByContent }: { rows: TrainerContentPerformanceRow[]; salesByContent: Record<string, number> }) {
  const activeRows = rows.filter((item) => (salesByContent[item.id] ?? item.purchase_count) > 0);

  if (!activeRows.length) {
    return (
      <div className="trainer-finance-empty">
        <strong>Активных доступов пока нет</strong>
        <p>После покупки ученики получат доступы, а карточки появятся здесь.</p>
      </div>
    );
  }

  return (
    <div className="trainer-sales-rail" aria-label="Доступы учеников">
      {activeRows.slice(0, 10).map((item) => {
        const accessCount = salesByContent[item.id] ?? item.purchase_count;
        return (
          <article className="trainer-sales-product-card" key={`access:${item.content_type}:${item.id}`}>
            <span className="trainer-finance-status trainer-finance-status-success">Активно</span>
            <strong>{item.title}</strong>
            <span>{contentTypeLabel(item.content_type)}</span>
            <small>{accessCount} активных доступов</small>
          </article>
        );
      })}
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
      setMessage(error instanceof Error ? error.message : 'Не удалось загрузить продажи');
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
  const conversionRate = useMemo(() => {
    const views = state?.overview.performance.total_views || 0;
    const purchases = state?.overview.performance.total_purchases || 0;
    return views ? (purchases / views) * 100 : 0;
  }, [state]);
  const salesByContent = useMemo(() => {
    return (state?.sales.results || []).reduce<Record<string, number>>((acc, sale) => {
      acc[sale.matched_content_id] = (acc[sale.matched_content_id] || 0) + sale.quantity;
      return acc;
    }, {});
  }, [state?.sales.results]);
  const averageOrder = state?.sales.summary.purchased_units
    ? Number(state.overview.sales.gross_order_sales || 0) / state.sales.summary.purchased_units
    : 0;
  const activeAccesses = state?.overview.performance.total_purchases || 0;

  return (
    <section className="trainer-sales-workbench">
      <section className="trainer-sales-hero">
        <div>
          <h2>Продажи</h2>
          <p>Контроль оплат, возвратов и доступа учеников.</p>
        </div>
        <div className="trainer-finance-hero-total">
          <span>Выручка за период</span>
          <strong>{money(state?.revenue.revenue.net_revenue, currency)}</strong>
          <small>{state?.sales.summary.matched_sales || 0} заказов · {refundTransactions.length} возвратов · {activeAccesses} доступов</small>
        </div>
      </section>

      <section className="trainer-finance-toolbar" aria-label="Фильтры продаж">
        <label className="trainer-finance-field">
          <span>Период</span>
          <select value={days} onChange={(event) => setDays(Number(event.target.value))}>
            {DAY_OPTIONS.map((option) => <option key={option} value={option}>{option} дней</option>)}
          </select>
        </label>
        <button type="button" className="premium-secondary-button" onClick={() => void load()} disabled={loading}>
          {loading ? 'Загружаем' : 'Обновить'}
        </button>
        <Link href="/trainer/dashboard/revenue" className="premium-secondary-button">Финансы</Link>
      </section>

      {message ? <div className="trainer-finance-message"><strong>Не удалось обновить продажи</strong><p>{message}</p></div> : null}
      {loading && !state ? <div className="trainer-finance-message"><strong>Загружаем продажи</strong><p>Собираем оплаты, возвраты и доступы учеников.</p></div> : null}

      {state ? (
        <>
          <section className="trainer-finance-kpi-grid" aria-label="Показатели продаж">
            <KpiCard label="Выручка" value={money(state.revenue.revenue.net_revenue, currency)} hint={`${days} дней`} />
            <KpiCard label="Оплаты" value={state.sales.summary.purchased_units} hint={`${state.sales.summary.matched_sales} заказов`} />
            <KpiCard label="Средний чек" value={money(averageOrder, currency)} />
            <KpiCard label="Возвраты" value={money(state.revenue.revenue.refunds, currency)} hint={`${refundTransactions.length} операций`} />
            <KpiCard label="Активные доступы" value={activeAccesses} hint={`Конверсия ${percent(conversionRate)}`} />
          </section>

          <section className="trainer-finance-workspace">
            <div className="trainer-finance-main">
              <article className="trainer-sales-card">
                <h3>Лучшие продукты</h3>
                <ProductRail rows={state.content.results} currency={currency} />
              </article>

              <article className="trainer-sales-card">
                <h3>Последние продажи</h3>
                <SalesTimeline rows={state.sales.results} currency={currency} />
              </article>
            </div>

            <aside className="trainer-finance-sidebar">
              <article className="trainer-sales-card">
                <h3>Возвраты и риски</h3>
                <RefundPanel rows={refundTransactions} currency={currency} />
              </article>

              <article className="trainer-sales-card">
                <h3>Доступ учеников</h3>
                <AccessPanel rows={state.content.results} salesByContent={salesByContent} />
              </article>
            </aside>
          </section>
        </>
      ) : null}
    </section>
  );
}
