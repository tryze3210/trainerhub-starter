'use client';

import { useEffect, useMemo, useState } from 'react';

import {
  getTrainerAnalyticsOverview,
  getTrainerContentAnalytics,
  getTrainerSalesAnalytics,
  type TrainerAnalyticsOverview,
  type TrainerContentAnalyticsResponse,
  type TrainerContentPerformanceRow,
  type TrainerSalesAnalyticsResponse,
} from '@/modules/trainer-analytics/api';

const DAY_OPTIONS = [7, 30, 90, 180];

type ContentTypeFilter = 'all' | 'video' | 'product';
type SortMode = 'net_revenue' | 'purchase_count' | 'views_count' | 'conversion_rate';

function formatMoney(value: string | null | undefined, currency = 'RUB') {
  const amount = Number(value || 0);
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
  }).format(Number.isFinite(amount) ? amount : 0);
}

function formatDate(value: string | null | undefined) {
  if (!value) return 'Дата не указана';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(date);
}

function percent(value?: string | number | null) {
  const parsed = Number(value ?? 0);
  if (!Number.isFinite(parsed)) return '0%';
  return `${parsed.toFixed(1)}%`;
}

function contentTypeLabel(value?: string | null) {
  if (value === 'video') return 'Видео';
  if (value === 'product') return 'Продукт';
  return 'Контент';
}

function statusLabel(value?: string | null) {
  const status = (value || '').toLowerCase();
  if (status === 'published' || status === 'paid' || status === 'completed') return 'Опубликовано';
  if (status === 'draft') return 'Черновик';
  if (status === 'review' || status === 'submitted' || status === 'under_review') return 'На проверке';
  if (status === 'refunded') return 'Возврат';
  if (status === 'failed') return 'Ошибка';
  return 'Требуется проверка';
}

function statusTone(value?: string | null) {
  const status = (value || '').toLowerCase();
  if (['published', 'paid', 'completed'].includes(status)) return 'success';
  if (['draft', 'review', 'submitted', 'under_review'].includes(status)) return 'warning';
  if (['refunded', 'failed', 'cancelled'].includes(status)) return 'danger';
  return 'neutral';
}

function statusClass(value?: string | null) {
  return `trainer-finance-status trainer-finance-status-${statusTone(value)}`;
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

function sortContent(rows: TrainerContentPerformanceRow[], sortBy: SortMode) {
  return [...rows].sort((left, right) => Number(right[sortBy] || 0) - Number(left[sortBy] || 0));
}

export function TrainerContentAnalyticsDashboard() {
  const [days, setDays] = useState(30);
  const [contentType, setContentType] = useState<ContentTypeFilter>('all');
  const [sortBy, setSortBy] = useState<SortMode>('net_revenue');
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
  const contentRows = useMemo(() => sortContent(content?.results || overview?.top_content || [], sortBy), [content?.results, overview?.top_content, sortBy]);
  const conversion = overview?.performance.total_views
    ? (overview.performance.total_purchases / overview.performance.total_views) * 100
    : 0;

  return (
    <section className="trainer-analytics-workbench">
      <section className="trainer-analytics-hero">
        <div>
          <h2>Аналитика контента</h2>
          <p>Продажи, просмотры и конверсия по материалам.</p>
        </div>
        <div className="trainer-finance-hero-total">
          <span>Чистая выручка</span>
          <strong>{formatMoney(overview?.performance.net_revenue, currency)}</strong>
          <small>{overview?.performance.total_purchases || 0} покупок · {overview?.performance.total_views || 0} просмотров</small>
        </div>
      </section>

      <section className="trainer-finance-toolbar" aria-label="Фильтры аналитики">
        <label className="trainer-finance-field">
          <span>Период</span>
          <select value={days} onChange={(event) => setDays(Number(event.target.value))}>
            {DAY_OPTIONS.map((option) => <option key={option} value={option}>{option} дней</option>)}
          </select>
        </label>
        <label className="trainer-finance-field">
          <span>Тип контента</span>
          <select value={contentType} onChange={(event) => setContentType(event.target.value as ContentTypeFilter)}>
            <option value="all">Все материалы</option>
            <option value="video">Видео</option>
            <option value="product">Продукты</option>
          </select>
        </label>
        <label className="trainer-finance-field">
          <span>Сортировка</span>
          <select value={sortBy} onChange={(event) => setSortBy(event.target.value as SortMode)}>
            <option value="net_revenue">По выручке</option>
            <option value="purchase_count">По покупкам</option>
            <option value="views_count">По просмотрам</option>
            <option value="conversion_rate">По конверсии</option>
          </select>
        </label>
      </section>

      {loading ? <div className="trainer-finance-message"><strong>Загружаем аналитику</strong><p>Собираем просмотры, покупки и выручку по материалам.</p></div> : null}
      {error ? <div className="trainer-finance-message"><strong>Аналитика недоступна</strong><p>{error}</p></div> : null}

      {overview ? (
        <section className="trainer-finance-kpi-grid" aria-label="Показатели контента">
          <KpiCard label="Чистая выручка" value={formatMoney(overview.performance.net_revenue, currency)} />
          <KpiCard label="Валовая выручка" value={formatMoney(overview.performance.gross_revenue, currency)} />
          <KpiCard label="Покупки" value={overview.performance.total_purchases} />
          <KpiCard label="Просмотры" value={overview.performance.total_views} />
          <KpiCard label="Конверсия" value={percent(conversion)} />
        </section>
      ) : null}

      <section className="trainer-analytics-content-grid">
        <div className="trainer-finance-main">
          <article className="trainer-analytics-insight-card">
            <h3>Лучший контент</h3>
            {contentRows.length ? (
              <div className="trainer-finance-rail" aria-label="Лучший контент">
                {contentRows.slice(0, 14).map((row) => {
                  const conversionValue = Math.min(100, Math.max(0, Number(row.conversion_rate || 0)));
                  return (
                    <article className="trainer-analytics-content-card" key={`${row.content_type}:${row.id}`}>
                      <span className={statusClass(row.status)}>{statusLabel(row.status)}</span>
                      <strong>{row.title}</strong>
                      <span>{contentTypeLabel(row.content_type)} · {row.views_count} просмотров</span>
                      <span>{row.purchase_count} покупок · {formatMoney(row.net_revenue, row.currency || currency)}</span>
                      <small>Конверсия {percent(row.conversion_rate)}</small>
                      <div className="trainer-analytics-progress"><span style={{ width: `${conversionValue}%` }} /></div>
                    </article>
                  );
                })}
              </div>
            ) : (
              <div className="trainer-finance-empty">
                <strong>Данных по контенту пока нет</strong>
                <p>Опубликуйте материалы и дождитесь первых просмотров или покупок.</p>
              </div>
            )}
          </article>

          <article className="trainer-analytics-insight-card">
            <h3>Последние продажи</h3>
            <div className="trainer-finance-timeline">
              {(sales?.results || []).map((sale) => (
                <article className="trainer-sales-timeline-card" key={`${sale.order_id}:${sale.item_id}`}>
                  <div className="trainer-finance-row">
                    <div>
                      <strong>{sale.title}</strong>
                      <span className="trainer-finance-muted">{contentTypeLabel(sale.matched_content_type)} · {formatDate(sale.created_at)}</span>
                    </div>
                    <span className={statusClass(sale.order_status)}>{statusLabel(sale.order_status)}</span>
                  </div>
                  <div className="trainer-finance-row">
                    <span>Покупатель</span>
                    <strong>{sale.quantity} шт. · {formatMoney(sale.total_price, sale.currency || currency)}</strong>
                  </div>
                </article>
              ))}
              {!loading && !sales?.results.length ? (
                <div className="trainer-finance-empty">
                  <strong>Продаж за выбранный период пока нет</strong>
                  <p>Проверьте период или откройте опубликованные материалы в каталоге.</p>
                </div>
              ) : null}
            </div>
          </article>
        </div>

        <aside className="trainer-finance-sidebar">
          <article className="trainer-analytics-insight-card">
            <h3>Качество данных</h3>
            <p className="trainer-finance-muted">
              Часть продаж сопоставляется по внутреннему идентификатору материала. Если материал был переименован, аналитика сохраняет связь с заказом.
            </p>
            {overview?.notes?.length ? overview.notes.map((note) => <p key={note}>{note}</p>) : <p>Критичных предупреждений по данным нет.</p>}
          </article>

          <article className="trainer-analytics-insight-card">
            <h3>Каталог</h3>
            <div className="trainer-finance-kpi-grid">
              <KpiCard label="Видео" value={overview?.counts.videos || 0} hint={`${overview?.counts.published_videos || 0} опубликовано`} />
              <KpiCard label="Продукты" value={overview?.counts.products || 0} hint={`${overview?.counts.published_products || 0} опубликовано`} />
              <KpiCard label="Бесплатные видео" value={overview?.counts.free_videos || 0} />
              <KpiCard label="Платные продукты" value={overview?.counts.paid_products || 0} />
            </div>
          </article>
        </aside>
      </section>
    </section>
  );
}
