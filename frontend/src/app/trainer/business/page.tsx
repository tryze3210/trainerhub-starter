'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { trainersApi } from '@/lib/api';
import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import type { TrainerBusinessDashboard } from '@/types/api';

const dayOptions = [7, 30, 90];

function formatMoney(value?: string | number | null, currency = 'RUB') {
  const amount = Number(value || 0);
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(Number.isFinite(amount) ? amount : 0);
}

function formatDateTime(value?: string | null) {
  if (!value) return 'Дата не указана';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

function formatPercent(value?: string | number | null) {
  const amount = Number(value || 0);
  return `${Number.isFinite(amount) ? Math.round(amount) : 0}%`;
}

function mapTrainerApplicationStatusLabel(status?: string | null) {
  const labels: Record<string, string> = {
    draft: 'Черновик',
    submitted: 'Отправлена',
    under_review: 'На проверке',
    approved: 'Одобрена',
    changes_requested: 'Нужны правки',
    rejected: 'Отклонена',
  };
  return labels[status || ''] || 'Не проверено';
}

function mapReadinessStatusLabel(status?: string | null) {
  const labels: Record<string, string> = {
    ready: 'Готово',
    done: 'Готово',
    approved: 'Одобрено',
    paid: 'Оплачено',
    healthy: 'Норма',
    attention: 'Требует внимания',
    blocked: 'Заблокировано',
    blocker: 'Блокер',
    critical: 'Критично',
    rejected: 'Отклонено',
    warning: 'Требует внимания',
    pending: 'Ожидает',
  };
  return labels[status || ''] || 'Не проверено';
}

function mapStepStatusLabel(status?: string | null) {
  const labels: Record<string, string> = {
    completed: 'Готово',
    blocked: 'Нужно исправить',
    open: 'Открыто',
  };
  return labels[status || ''] || 'Открыто';
}

function mapRoleLabel(role?: string | null) {
  const labels: Record<string, string> = {
    customer: 'Клиент',
    trainer: 'Тренер',
    admin: 'Администратор',
  };
  return labels[role || ''] || 'Пользователь';
}

function mapProductTypeLabel(type?: string | null) {
  const labels: Record<string, string> = {
    video: 'Видео',
    course: 'Курс',
    program: 'Программа',
    product: 'Продукт',
    bundle: 'Набор',
  };
  return labels[type || ''] || 'Материал';
}

function mapPayoutStatusLabel(status?: string | null) {
  const labels: Record<string, string> = {
    pending: 'На проверке',
    approved: 'Одобрено',
    processing: 'В обработке',
    paid: 'Выплачено',
    rejected: 'Отклонено',
    cancelled: 'Отменено',
    failed: 'Ошибка выплаты',
  };
  return labels[status || ''] || 'Не проверено';
}

function mapModerationStatusLabel(status?: string | null) {
  const labels: Record<string, string> = {
    open: 'Открыто',
    pending: 'Ожидает',
    under_review: 'На проверке',
    approved: 'Одобрено',
    rejected: 'Отклонено',
    blocked: 'Заблокировано',
    resolved: 'Решено',
    closed: 'Закрыто',
    critical: 'Критично',
    warning: 'Требует внимания',
  };
  return labels[status || ''] || 'Не проверено';
}

function getBadgeTone(status?: string | null) {
  if (['ready', 'done', 'approved', 'paid', 'healthy', 'completed', 'resolved', 'closed'].includes(status || '')) return 'success';
  if (['blocked', 'blocker', 'critical', 'rejected', 'failed'].includes(status || '')) return 'danger';
  if (['warning', 'pending', 'under_review', 'changes_requested', 'processing', 'submitted', 'open'].includes(status || '')) return 'warning';
  return 'neutral';
}

function shortId(value?: string | null) {
  if (!value) return 'без номера';
  return value.length > 10 ? `${value.slice(0, 6)}…${value.slice(-4)}` : value;
}

function caseText(item: Record<string, unknown>, key: string, fallback = '') {
  const value = item[key];
  return typeof value === 'string' && value.trim() ? value : fallback;
}

export default function TrainerBusinessPage() {
  const [days, setDays] = useState(30);
  const [dashboard, setDashboard] = useState<TrainerBusinessDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function load(selectedDays = days) {
    try {
      setLoading(true);
      setError('');
      setDashboard(await trainersApi.getTrainerBusinessDashboard(selectedDays));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить бизнес-сводку');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load(days);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days]);

  const currency = dashboard?.payouts.balance.currency || 'RUB';
  const latestRevenue = useMemo(() => (dashboard?.commerce.revenue_series || []).slice(-10), [dashboard]);
  const averageOrderPercent = dashboard?.commerce.revenue_period
    ? (Number(dashboard.commerce.avg_order_value || 0) / Math.max(Number(dashboard.commerce.revenue_period || 0), 1)) * 100
    : 0;

  const kpis = [
    { label: 'Выручка периода', value: formatMoney(dashboard?.commerce.revenue_period, currency), note: `${days} дней` },
    { label: 'Заказы', value: dashboard?.commerce.period_orders_count || 0, note: `${dashboard?.commerce.order_items_period_count || 0} позиций` },
    { label: 'Покупатели', value: dashboard?.commerce.customers_count || 0, note: 'уникальные клиенты' },
    { label: 'Средний чек', value: formatMoney(dashboard?.commerce.avg_order_value, currency), note: formatPercent(averageOrderPercent) },
    { label: 'Доступно к выплате', value: formatMoney(dashboard?.payouts.balance.available_amount, currency), note: 'можно запросить' },
    { label: 'В резерве', value: formatMoney(dashboard?.payouts.balance.reserved_amount, currency), note: 'ожидает релиза' },
    { label: 'Заработано всего', value: formatMoney(dashboard?.payouts.balance.lifetime_earned_amount, currency), note: 'за всё время' },
    { label: 'Активные выплаты', value: dashboard?.payouts.active_requests_count || 0, note: 'в работе' },
  ];

  return (
    <ProtectedPage title="Бизнес" description="Сводка тренера доступна только после авторизации.">
      <TrainerDashboardShell
        title="Бизнес"
        description="Сводка по выручке, выплатам, контенту и рискам"
      >
        <div className="trainer-business-workbench">
          <section className="trainer-business-hero">
            <div>
              <span className="trainer-business-eyebrow">Бизнес-центр</span>
              <h2>Бизнес</h2>
              <p>Сводка по выручке, выплатам, контенту и рискам</p>
              <div className="trainer-business-actions">
                {dayOptions.map((value) => (
                  <button
                    key={value}
                    type="button"
                    className={days === value ? 'premium-primary-button' : 'premium-secondary-button'}
                    onClick={() => setDays(value)}
                  >
                    {value} дней
                  </button>
                ))}
                <Link className="premium-secondary-button" href="/trainer/dashboard/sales">Продажи</Link>
                <Link className="premium-secondary-button" href="/trainer/dashboard/revenue">Финансы</Link>
                <Link className="premium-secondary-button" href="/trainer/dashboard/payouts">Выплаты</Link>
              </div>
            </div>
            <div className="trainer-business-hero-total">
              <span>Выручка периода</span>
              <strong>{formatMoney(dashboard?.commerce.revenue_period, currency)}</strong>
              <small>
                {dashboard?.commerce.period_orders_count || 0} заказов · {dashboard?.commerce.customers_count || 0} покупателей · средний чек {formatMoney(dashboard?.commerce.avg_order_value, currency)}
              </small>
            </div>
          </section>

          {loading ? (
            <section className="trainer-business-panel">
              <h3>Загружаем бизнес-сводку</h3>
              <p className="trainer-business-muted">Собираем выручку, выплаты, контент и риски.</p>
            </section>
          ) : null}

          {error ? (
            <section className="trainer-business-panel trainer-business-alert">
              <h3>Не удалось загрузить бизнес-сводку</h3>
              <p>{error}</p>
              <button className="premium-secondary-button" type="button" onClick={() => void load()}>
                Повторить
              </button>
            </section>
          ) : null}

          <section className="trainer-business-kpi-grid">
            {kpis.map((item) => (
              <article className="trainer-business-card" key={item.label}>
                <span>{item.label}</span>
                <strong>{item.value}</strong>
                <small>{item.note}</small>
              </article>
            ))}
          </section>

          {dashboard ? (
            <section className="trainer-business-layout">
              <div className="trainer-business-main">
                <section className="trainer-business-panel">
                  <div className="trainer-business-panel-head">
                    <div>
                      <h3>Готовность бизнеса</h3>
                      <p>Проверки, которые влияют на продажи, выплаты и публикацию продуктов.</p>
                    </div>
                    <span className={`trainer-business-status trainer-business-status-${getBadgeTone(dashboard.readiness.status)}`}>
                      {mapReadinessStatusLabel(dashboard.readiness.status)}
                    </span>
                  </div>
                  <div className="trainer-business-readiness-grid">
                    {dashboard.readiness.checks.map((check) => (
                      <article className="trainer-business-readiness-card" key={check.code}>
                        <strong>{check.title}</strong>
                        <span className={`trainer-business-status trainer-business-status-${getBadgeTone(check.status)}`}>
                          {mapReadinessStatusLabel(check.status)}
                        </span>
                      </article>
                    ))}
                  </div>
                </section>

                <section className="trainer-business-panel">
                  <div className="trainer-business-panel-head">
                    <div>
                      <h3>Контент и продукты</h3>
                      <p>Публикации, черновики и оплаченные позиции.</p>
                    </div>
                    <Link className="premium-secondary-button" href="/trainer/dashboard/products">Открыть студию продуктов</Link>
                  </div>
                  <div className="trainer-business-kpi-grid">
                    <article className="trainer-business-card"><span>Черновики</span><strong>{dashboard.content.drafts.total}</strong><small>видео, программы и наборы</small></article>
                    <article className="trainer-business-card"><span>Опубликовано</span><strong>{dashboard.content.published.total}</strong><small>доступно покупателям</small></article>
                    <article className="trainer-business-card"><span>На проверке</span><strong>{dashboard.content.pending_review_count}</strong><small>ожидает модерацию</small></article>
                    <article className="trainer-business-card"><span>Позиции заказов</span><strong>{dashboard.commerce.order_items_count}</strong><small>за всё время</small></article>
                  </div>
                </section>

                <section className="trainer-business-panel">
                  <h3>Динамика выручки</h3>
                  <div className="trainer-business-timeline">
                    {latestRevenue.map((point) => (
                      <article className="trainer-business-timeline-item" key={point.date}>
                        <span>{point.date}</span>
                        <strong>{formatMoney(point.revenue, currency)}</strong>
                        <small>{point.orders_count} заказов</small>
                      </article>
                    ))}
                    {!latestRevenue.length ? (
                      <div className="trainer-business-empty">Пока нет оплаченных заказов за выбранный период.</div>
                    ) : null}
                  </div>
                </section>

                <section className="trainer-business-panel">
                  <h3>Лучшие продукты</h3>
                  <div className="trainer-business-product-rail">
                    {dashboard.commerce.top_products.map((item) => (
                      <article className="trainer-business-card" key={`${item.item_type}-${item.title}`}>
                        <span>{mapProductTypeLabel(item.item_type)}</span>
                        <strong>{item.title}</strong>
                        <small>{item.orders_count} заказов · {formatMoney(item.revenue, currency)}</small>
                      </article>
                    ))}
                    {!dashboard.commerce.top_products.length ? (
                      <div className="trainer-business-empty">После первых продаж здесь появятся продукты с лучшей выручкой.</div>
                    ) : null}
                  </div>
                </section>
              </div>

              <aside className="trainer-business-sidebar">
                <section className="trainer-business-panel">
                  <div className="trainer-business-panel-head">
                    <div>
                      <h3>Последние заявки на выплаты</h3>
                      <p>Суммы, реквизиты и текущий этап обработки.</p>
                    </div>
                    <Link className="premium-secondary-button" href="/trainer/dashboard/payouts">Все выплаты</Link>
                  </div>
                  <div className="trainer-business-timeline">
                    {dashboard.payouts.latest_requests.map((payout) => (
                      <article className="trainer-business-timeline-item" key={payout.id}>
                        <span>{shortId(payout.id)} · {formatDateTime(payout.requested_at)}</span>
                        <strong>{formatMoney(payout.amount, payout.currency)}</strong>
                        <small>{payout.destination_masked || 'Реквизиты не указаны'}</small>
                        <span className={`trainer-business-status trainer-business-status-${getBadgeTone(payout.status)}`}>
                          {mapPayoutStatusLabel(payout.status)}
                        </span>
                      </article>
                    ))}
                    {!dashboard.payouts.latest_requests.length ? (
                      <div className="trainer-business-empty">Заявок на выплаты пока нет.</div>
                    ) : null}
                  </div>
                </section>

                <section className="trainer-business-panel">
                  <h3>Риски и модерация</h3>
                  <div className="trainer-business-risk-grid">
                    <article className="trainer-business-risk-card">
                      <span>Открытые кейсы</span>
                      <strong>{dashboard.moderation.open_cases_count}</strong>
                    </article>
                    <article className="trainer-business-risk-card">
                      <span>Риск-флаги</span>
                      <strong>{dashboard.moderation.risk_flags_count}</strong>
                    </article>
                  </div>
                  <div className="trainer-business-timeline">
                    {dashboard.moderation.latest_cases.map((item, index) => {
                      const status = caseText(item, 'status', 'unknown');
                      return (
                        <article className="trainer-business-timeline-item" key={caseText(item, 'id', String(index))}>
                          <span>{caseText(item, 'reason', 'Кейс модерации')}</span>
                          <strong>{caseText(item, 'title', 'Проверка')}</strong>
                          <small>{caseText(item, 'created_at') ? formatDateTime(caseText(item, 'created_at')) : 'Дата не указана'}</small>
                          <span className={`trainer-business-status trainer-business-status-${getBadgeTone(status)}`}>
                            {mapModerationStatusLabel(status)}
                          </span>
                        </article>
                      );
                    })}
                    {!dashboard.moderation.latest_cases.length ? (
                      <div className="trainer-business-empty">Открытых кейсов модерации нет.</div>
                    ) : null}
                  </div>
                </section>

                <section className="trainer-business-panel">
                  <h3>Статус заявки</h3>
                  <article className="trainer-business-readiness-card">
                    <strong>{mapTrainerApplicationStatusLabel(dashboard.application?.status)}</strong>
                    <span>{dashboard.application?.brand_name || dashboard.application?.legal_name || 'Профиль пока не заполнен'}</span>
                  </article>
                  <article className="trainer-business-readiness-card">
                    <strong>{mapRoleLabel('trainer')}</strong>
                    <span>{mapStepStatusLabel(dashboard.profile.public_profile ? 'completed' : 'open')}</span>
                  </article>
                </section>
              </aside>
            </section>
          ) : null}
        </div>
      </TrainerDashboardShell>
    </ProtectedPage>
  );
}
