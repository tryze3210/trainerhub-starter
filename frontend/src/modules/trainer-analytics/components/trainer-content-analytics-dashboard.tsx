'use client';

import { useEffect, useMemo, useState } from 'react';

import {
  getTrainerAnalyticsOverview,
  getTrainerContentAnalytics,
  getTrainerSalesAnalytics,
  type TrainerAnalyticsOverview,
  type TrainerContentAnalyticsResponse,
  type TrainerSalesAnalyticsResponse,
} from '@/modules/trainer-analytics/api';

const DAY_OPTIONS = [7, 30, 90, 180];

function formatMoney(value: string | null | undefined, currency = 'RUB') {
  const amount = Number(value || 0);
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
  }).format(Number.isFinite(amount) ? amount : 0);
}

function formatDate(value: string | null | undefined) {
  if (!value) return '—';
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(new Date(value));
}

function StatCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <article className="card stack" style={{ gap: 8 }}>
      <span className="muted">{label}</span>
      <strong className="title-md">{value}</strong>
      {hint ? <span className="muted">{hint}</span> : null}
    </article>
  );
}

export function TrainerContentAnalyticsDashboard() {
  const [days, setDays] = useState(30);
  const [contentType, setContentType] = useState<'all' | 'video' | 'product'>('all');
  const [overview, setOverview] = useState<TrainerAnalyticsOverview | null>(null);
  const [content, setContent] = useState<TrainerContentAnalyticsResponse | null>(null);
  const [sales, setSales] = useState<TrainerSalesAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError(null);

    Promise.all([
      getTrainerAnalyticsOverview(days),
      getTrainerContentAnalytics(contentType, days, 50),
      getTrainerSalesAnalytics(days, 25),
    ])
      .then(([overviewPayload, contentPayload, salesPayload]) => {
        if (!mounted) return;
        setOverview(overviewPayload);
        setContent(contentPayload);
        setSales(salesPayload);
      })
      .catch((err) => {
        if (!mounted) return;
        setError(err instanceof Error ? err.message : 'Не удалось загрузить аналитику контента.');
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [days, contentType]);

  const currency = overview?.currency || content?.currency || sales?.currency || 'RUB';
  const topContent = useMemo(() => overview?.top_content || [], [overview]);

  return (
    <div className="stack" style={{ gap: 24 }}>
      <section className="card stack" style={{ gap: 16 }}>
        <div className="grid-2" style={{ alignItems: 'end' }}>
          <div className="stack" style={{ gap: 6 }}>
            <span className="badge">v8.43</span>
            <h2 className="title-md">Content performance analytics</h2>
            <p className="muted">
              Продажи, просмотры, конверсия и выручка по видео и продуктам тренера.
            </p>
          </div>
          <div className="grid-2">
            <label className="stack" style={{ gap: 6 }}>
              <span className="muted">Период</span>
              <select value={days} onChange={(event) => setDays(Number(event.target.value))}>
                {DAY_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option} дней
                  </option>
                ))}
              </select>
            </label>
            <label className="stack" style={{ gap: 6 }}>
              <span className="muted">Тип</span>
              <select value={contentType} onChange={(event) => setContentType(event.target.value as typeof contentType)}>
                <option value="all">Все</option>
                <option value="video">Видео</option>
                <option value="product">Продукты</option>
              </select>
            </label>
          </div>
        </div>
      </section>

      {loading ? <div className="card muted">Загружаем аналитику…</div> : null}
      {error ? <div className="card danger">{error}</div> : null}

      {overview ? (
        <section className="grid-4">
          <StatCard label="Net revenue" value={formatMoney(overview.performance.net_revenue, currency)} />
          <StatCard label="Gross revenue" value={formatMoney(overview.performance.gross_revenue, currency)} />
          <StatCard label="Purchases" value={overview.performance.total_purchases} />
          <StatCard label="Views" value={overview.performance.total_views} />
        </section>
      ) : null}

      {overview ? (
        <section className="grid-3">
          <StatCard label="Videos" value={overview.counts.videos} hint={`${overview.counts.published_videos} published`} />
          <StatCard label="Products" value={overview.counts.products} hint={`${overview.counts.published_products} published`} />
          <StatCard label="Gross order sales" value={formatMoney(overview.sales.gross_order_sales, currency)} />
        </section>
      ) : null}

      <section className="card stack" style={{ gap: 16 }}>
        <div className="section-heading">
          <h2 className="title-md">Top content</h2>
          <span className="muted">По net revenue и покупкам</span>
        </div>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Content</th>
                <th>Status</th>
                <th>Views</th>
                <th>Purchases</th>
                <th>Conversion</th>
                <th>Net</th>
              </tr>
            </thead>
            <tbody>
              {(content?.results || topContent).map((row) => (
                <tr key={`${row.content_type}:${row.id}`}>
                  <td>
                    <strong>{row.title}</strong>
                    <br />
                    <span className="muted">{row.content_type} · {row.slug}</span>
                  </td>
                  <td><span className="badge secondary">{row.status}</span></td>
                  <td>{row.views_count}</td>
                  <td>{row.purchase_count}</td>
                  <td>{row.conversion_rate}</td>
                  <td>{formatMoney(row.net_revenue, row.currency || currency)}</td>
                </tr>
              ))}
              {!loading && !(content?.results || topContent).length ? (
                <tr>
                  <td colSpan={6} className="muted">Нет данных по контенту за выбранный период.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card stack" style={{ gap: 16 }}>
        <div className="section-heading">
          <h2 className="title-md">Recent sales</h2>
          <span className="muted">Order item matching по UUID/slug</span>
        </div>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Item</th>
                <th>Type</th>
                <th>Qty</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {(sales?.results || []).map((sale) => (
                <tr key={`${sale.order_id}:${sale.item_id}`}>
                  <td>{formatDate(sale.created_at)}</td>
                  <td>
                    <strong>{sale.title}</strong>
                    <br />
                    <span className="muted">{sale.order_status}</span>
                  </td>
                  <td>{sale.matched_content_type}</td>
                  <td>{sale.quantity}</td>
                  <td>{formatMoney(sale.total_price, sale.currency || currency)}</td>
                </tr>
              ))}
              {!loading && !sales?.results.length ? (
                <tr>
                  <td colSpan={5} className="muted">Продаж за выбранный период пока нет.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      {overview?.notes?.length ? (
        <section className="card stack" style={{ gap: 8 }}>
          <h2 className="title-md">Data notes</h2>
          {overview.notes.map((note) => (
            <p key={note} className="muted">{note}</p>
          ))}
        </section>
      ) : null}
    </div>
  );
}
