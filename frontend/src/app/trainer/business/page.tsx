'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { trainersApi } from '@/lib/api';
import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import {
  TrainerDashboardCard,
  TrainerEmptyState,
  TrainerErrorState,
  TrainerLoadingState,
  TrainerMetricCard,
  TrainerStatusBadge,
  type TrainerMetric,
} from '@/modules/trainer-cabinet/components';
import {
  formatTrainerMoney,
  trainerPayoutStatusLabel,
  trainerProductTypeLabel,
  trainerStatusLabel,
  trainerStatusTone,
} from '@/modules/trainer-cabinet/components/trainer-format';
import type { TrainerBusinessDashboard } from '@/types/api';

const dayOptions = [7, 30, 90];

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
      setError(err instanceof Error ? err.message : 'Не удалось загрузить данные');
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
  const metrics: TrainerMetric[] = [
    { label: 'Выручка периода', value: formatTrainerMoney(dashboard?.commerce.revenue_period, currency), tone: 'success' },
    { label: 'Заказы периода', value: dashboard?.commerce.period_orders_count || 0, tone: 'primary' },
    { label: 'Покупатели', value: dashboard?.commerce.customers_count || 0, tone: 'neutral' },
    { label: 'Средний чек', value: formatTrainerMoney(dashboard?.commerce.avg_order_value, currency), tone: 'primary' },
    { label: 'Доступно к выплате', value: formatTrainerMoney(dashboard?.payouts.balance.available_amount, currency), tone: 'success' },
    { label: 'В резерве', value: formatTrainerMoney(dashboard?.payouts.balance.reserved_amount, currency), tone: 'warning' },
    { label: 'Всего заработано', value: formatTrainerMoney(dashboard?.payouts.balance.lifetime_earned_amount, currency), tone: 'success' },
    { label: 'Активные заявки', value: dashboard?.payouts.active_requests_count || 0, tone: 'neutral' },
  ];

  return (
    <ProtectedPage title="Бизнес тренера" description="Бизнес-кабинет тренера доступен только после авторизации.">
      <TrainerDashboardShell
        title="Бизнес тренера"
        description="Выручка, заказы, покупатели, выплаты и риски в одном операционном обзоре."
      >
        <div className="trainer-page-actions">
          {dayOptions.map((value) => (
            <button key={value} type="button" className={days === value ? 'premium-primary-button' : 'premium-secondary-button'} onClick={() => setDays(value)}>
              {value} дней
            </button>
          ))}
        </div>

        {loading ? <TrainerLoadingState title="Загружаем бизнес-метрики" /> : null}
        {error ? <TrainerErrorState message={error} onRetry={() => void load()} /> : null}

        <div className="trainer-metric-grid">
          {metrics.map((metric) => <TrainerMetricCard key={metric.label} metric={metric} />)}
        </div>

        {dashboard ? (
          <div className="trainer-dashboard-grid">
            <TrainerDashboardCard title="Готовность бизнеса" description="Проверки, которые влияют на продажи и выплаты.">
              <div className="trainer-revenue-list">
                {dashboard.readiness.checks.map((check) => (
                  <div className="trainer-section-card" key={check.code}>
                    <strong>{check.title}</strong>
                    <TrainerStatusBadge tone={trainerStatusTone(check.status)}>{trainerStatusLabel(check.status)}</TrainerStatusBadge>
                  </div>
                ))}
              </div>
            </TrainerDashboardCard>

            <TrainerDashboardCard title="Контент и продажи" description="Инвентарь продуктов и оплаченные позиции.">
              <div className="trainer-business-grid">
                <TrainerMetricCard metric={{ label: 'Черновики', value: dashboard.content.drafts.total, tone: 'neutral' }} />
                <TrainerMetricCard metric={{ label: 'Опубликовано', value: dashboard.content.published.total, tone: 'success' }} />
                <TrainerMetricCard metric={{ label: 'На проверке', value: dashboard.content.pending_review_count, tone: 'warning' }} />
                <TrainerMetricCard metric={{ label: 'Позиции заказов', value: dashboard.commerce.order_items_count, tone: 'primary' }} />
              </div>
              <Link className="premium-secondary-button" href="/trainer/videos">Видео и материалы</Link>
            </TrainerDashboardCard>

            <TrainerDashboardCard title="Динамика выручки">
              <div className="trainer-revenue-list">
                {latestRevenue.map((point) => (
                  <div className="trainer-section-card" key={point.date}>
                    <strong>{point.date}</strong>
                    <span>{formatTrainerMoney(point.revenue, currency)}</span>
                    <small>{point.orders_count} заказов</small>
                  </div>
                ))}
                {!latestRevenue.length ? <TrainerEmptyState title="Пока нет оплаченных заказов за выбранный период." description="После первых продаж здесь появится динамика." /> : null}
              </div>
            </TrainerDashboardCard>

            <TrainerDashboardCard title="Лучшие продукты">
              <div className="trainer-product-list">
                {dashboard.commerce.top_products.map((item) => (
                  <div className="trainer-section-card" key={`${item.item_type}-${item.title}`}>
                    <strong>{item.title}</strong>
                    <span>{trainerProductTypeLabel(item.item_type)} · {item.orders_count} заказов</span>
                    <small>{formatTrainerMoney(item.revenue, currency)}</small>
                  </div>
                ))}
                {!dashboard.commerce.top_products.length ? <TrainerEmptyState title="Пока нет продаж по продуктам." description="Рейтинг появится после первых оплаченных заказов." /> : null}
              </div>
            </TrainerDashboardCard>

            <TrainerDashboardCard title="Заявки на выплаты" action={<Link className="premium-secondary-button" href="/trainer/dashboard/payouts">Все выплаты</Link>}>
              <div className="trainer-revenue-list">
                {dashboard.payouts.latest_requests.map((payout) => (
                  <div className="trainer-section-card" key={payout.id}>
                    <strong>{formatTrainerMoney(payout.amount, payout.currency)}</strong>
                    <span>{payout.destination_masked || 'способ выплаты не указан'}</span>
                    <TrainerStatusBadge tone={trainerStatusTone(payout.status)}>{trainerPayoutStatusLabel(payout.status)}</TrainerStatusBadge>
                  </div>
                ))}
                {!dashboard.payouts.latest_requests.length ? <TrainerEmptyState title="Заявок на выплаты пока нет." description="Когда баланс будет доступен, создайте заявку на выплату." actionHref="/trainer/dashboard/payouts" actionLabel="Открыть выплаты" /> : null}
              </div>
            </TrainerDashboardCard>

            <TrainerDashboardCard title="Модерация и риски">
              <div className="trainer-business-grid">
                <TrainerMetricCard metric={{ label: 'Открытые обращения', value: dashboard.moderation.open_cases_count, tone: dashboard.moderation.open_cases_count ? 'warning' : 'success' }} />
                <TrainerMetricCard metric={{ label: 'Риск-флаги', value: dashboard.moderation.risk_flags_count, tone: dashboard.moderation.risk_flags_count ? 'danger' : 'success' }} />
              </div>
            </TrainerDashboardCard>
          </div>
        ) : null}
      </TrainerDashboardShell>
    </ProtectedPage>
  );
}
