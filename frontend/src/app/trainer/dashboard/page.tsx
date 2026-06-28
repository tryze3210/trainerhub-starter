'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { checkoutApi, onboardingApi, paymentsApi, privateApi, trainersApi } from '@/lib/api';
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
  trainerProductTypeLabel,
  trainerStatusLabel,
  trainerStatusTone,
} from '@/modules/trainer-cabinet/components/trainer-format';
import type { OnboardingStatus, Order, Payment, TrainerCmsDashboard, TrainerProfile, TrainerRevenueDashboard } from '@/types/api';

type DashboardState = {
  onboarding: OnboardingStatus | null;
  profile: TrainerProfile | null;
  cms: TrainerCmsDashboard | null;
  payments: Payment[];
  orders: Order[];
  revenue: TrainerRevenueDashboard | null;
};

async function loadDashboardState(): Promise<DashboardState> {
  const [onboarding, profile, cmsPayload, payments, orders, revenue] = await Promise.all([
    onboardingApi.status().catch(() => null),
    trainersApi.getMyProfile().catch(() => null),
    trainersApi.getTrainerCmsDashboard().catch(() => null),
    paymentsApi.listPayments().catch(() => []),
    checkoutApi.listOrders().catch(() => []),
    privateApi.getTrainerRevenueDashboard().catch(() => null),
  ]);
  return {
    onboarding,
    profile,
    cms: Array.isArray(cmsPayload) ? cmsPayload[0] || null : cmsPayload,
    payments,
    orders,
    revenue,
  };
}

export default function TrainerDashboardPage() {
  const { user } = useAuthSession();
  const [state, setState] = useState<DashboardState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function load() {
    try {
      setLoading(true);
      setError('');
      setState(await loadDashboardState());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить данные');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const grossRevenue = useMemo(() => (state?.payments || []).reduce((sum, payment) => {
    const value = Number(payment.gross_amount || payment.amount || 0);
    return Number.isFinite(value) ? sum + value : sum;
  }, 0), [state]);
  const currency = state?.revenue?.summary.currency || 'RUB';
  const metrics: TrainerMetric[] = [
    { label: 'Готовность профиля', value: `${state?.onboarding?.summary.completion_percent || 0}%`, hint: 'Публичная карточка', tone: (state?.onboarding?.summary.completion_percent || 0) >= 100 ? 'success' : 'warning' },
    { label: 'Заказы', value: state?.orders.length || 0, hint: 'Все видимые заказы', tone: 'primary' },
    { label: 'Оплаты', value: state?.payments.length || 0, hint: 'Записи оплат', tone: 'primary' },
    { label: 'Оборот', value: formatTrainerMoney(grossRevenue, 'RUB'), hint: 'Общий оборот', tone: 'success' },
    { label: 'Опубликовано', value: state?.cms?.published_videos_count || 0, hint: 'Видео и продукты', tone: 'success' },
    { label: 'Черновики', value: state?.cms?.draft_videos_count || 0, hint: 'Готовятся к публикации', tone: 'neutral' },
  ];

  return (
    <ProtectedPage title="Обзор тренера" description="Кабинет тренера доступен только после авторизации.">
      <TrainerDashboardShell
        title="Обзор тренера"
        description="Следите за продажами, продуктами, учениками и выплатами из одного рабочего пространства."
      >
        {user?.active_role !== 'trainer' ? <TrainerErrorState message="Текущая сессия не является аккаунтом тренера." /> : null}
        {loading ? <TrainerLoadingState /> : null}
        {error ? <TrainerErrorState message={error} onRetry={() => void load()} /> : null}

        <div className="trainer-metric-grid">
          {metrics.map((metric) => <TrainerMetricCard key={metric.label} metric={metric} />)}
        </div>

        {state ? (
          <div className="trainer-dashboard-grid">
            <TrainerDashboardCard title="Следующее действие" description="Что быстрее всего улучшит продажи и готовность кабинета.">
              <div className="trainer-section-card">
                <h3>{state.profile ? 'Создать продукт' : 'Заполнить профиль'}</h3>
                <p>{state.profile ? 'Добавьте новый платный продукт или обновите существующие материалы.' : 'Профиль ещё не заполнен. Ученикам нужно видеть специализацию и описание.'}</p>
                <div className="trainer-page-actions">
                  <Link href={state.profile ? '/trainer/dashboard/products' : '/trainer/onboarding'} className="premium-primary-button">
                    {state.profile ? 'Создать продукт' : 'Заполнить профиль'}
                  </Link>
                  <Link href="/trainer/dashboard/sales" className="premium-secondary-button">Открыть продажи</Link>
                  <Link href="/trainer/dashboard/payouts" className="premium-secondary-button">Посмотреть выплаты</Link>
                </div>
              </div>
            </TrainerDashboardCard>

            <TrainerDashboardCard title="Публичный профиль" description="То, что видят потенциальные ученики.">
              {state.profile ? (
                <div className="trainer-section-card">
                  <TrainerStatusBadge tone="success">Профиль активен</TrainerStatusBadge>
                  <h3>{state.profile.display_name || 'Тренер'}</h3>
                  <p><strong>Публичный адрес:</strong> {state.profile.slug || 'Не указан'}</p>
                  <p><strong>Краткое описание:</strong> {state.profile.headline || 'Профиль ещё не заполнен'}</p>
                  <p><strong>О тренере:</strong> {state.profile.bio || 'Профиль ещё не заполнен'}</p>
                </div>
              ) : (
                <TrainerEmptyState title="Профиль ещё не заполнен" description="Заполните публичный профиль, чтобы ученики понимали вашу специализацию." actionHref="/trainer/onboarding" actionLabel="Заполнить профиль" />
              )}
            </TrainerDashboardCard>

            <TrainerDashboardCard title="Контент" description="Сводка по опубликованным и готовящимся материалам.">
              <div className="trainer-business-grid">
                <TrainerMetricCard metric={{ label: 'Черновики', value: state.cms?.draft_videos_count || 0, tone: 'neutral' }} />
                <TrainerMetricCard metric={{ label: 'Опубликованные видео', value: state.cms?.published_videos_count || 0, tone: 'success' }} />
                <TrainerMetricCard metric={{ label: 'На проверке', value: state.cms?.pending_review_count || 0, tone: 'warning' }} />
                <TrainerMetricCard metric={{ label: 'Продажи', value: state.cms?.total_sales_count || 0, tone: 'primary' }} />
              </div>
            </TrainerDashboardCard>

            <TrainerDashboardCard title="Динамика дохода" description="Последние начисления по оплатам.">
              <div className="trainer-revenue-list">
                {(state.revenue?.revenue_series || []).slice(-8).map((point) => (
                  <div className="trainer-section-card" key={point.date}>
                    <strong>{point.date}</strong>
                    <span>{formatTrainerMoney(point.accrual_amount, currency)}</span>
                    <small>{point.orders_count} заказов</small>
                  </div>
                ))}
                {!(state.revenue?.revenue_series || []).length ? <TrainerEmptyState title="Пока нет оплаченных заказов" description="График появится после первых продаж." /> : null}
              </div>
            </TrainerDashboardCard>

            <TrainerDashboardCard title="Лучшие продукты" description="Материалы с максимальной выручкой.">
              <div className="trainer-product-list">
                {(state.revenue?.top_products || []).map((item) => (
                  <div className="trainer-section-card" key={`${item.item_type}-${item.title}`}>
                    <strong>{item.title}</strong>
                    <span>{trainerProductTypeLabel(item.item_type)}</span>
                    <small>{formatTrainerMoney(item.revenue, currency)}</small>
                  </div>
                ))}
                {!(state.revenue?.top_products || []).length ? <TrainerEmptyState title="Рейтинга пока нет" description="Данные появятся после первых оплаченных продуктов." /> : null}
              </div>
            </TrainerDashboardCard>
          </div>
        ) : null}
      </TrainerDashboardShell>
    </ProtectedPage>
  );
}
