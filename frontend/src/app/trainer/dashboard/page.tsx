'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { checkoutApi, onboardingApi, paymentsApi, privateApi, trainersApi } from '@/lib/api';
import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import { trainerProductTypeLabel } from '@/modules/trainer-cabinet/components/trainer-format';
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

function formatMoney(value?: string | number | null, currency = 'RUB') {
  const amount = Number(value || 0);
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(Number.isFinite(amount) ? amount : 0);
}

function formatPercent(value?: string | number | null) {
  const amount = Number(value || 0);
  return `${Number.isFinite(amount) ? Math.round(amount) : 0}%`;
}

function shortText(value?: string | null, fallback = 'Данные пока не заполнены') {
  return value && value.trim() ? value : fallback;
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
      setError(err instanceof Error ? err.message : 'Не удалось загрузить кабинет тренера');
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
  const profileProgress = state?.onboarding?.summary.completion_percent || 0;
  const publishedCount = state?.cms?.published_videos_count || 0;
  const draftCount = state?.cms?.draft_videos_count || 0;
  const mainValue = state?.revenue?.summary.available_amount
    ? formatMoney(state.revenue.summary.available_amount, currency)
    : grossRevenue > 0
      ? formatMoney(grossRevenue, currency)
      : formatPercent(profileProgress);

  const kpis = [
    { label: 'Готовность профиля', value: formatPercent(profileProgress), hint: 'публичная карточка' },
    { label: 'Заказы', value: state?.orders.length || 0, hint: 'видимые заказы' },
    { label: 'Оплаты', value: state?.payments.length || 0, hint: 'записи оплат' },
    { label: 'Оборот', value: formatMoney(grossRevenue, currency), hint: 'по оплатам' },
    { label: 'Опубликовано', value: publishedCount, hint: 'материалы' },
    { label: 'Черновики', value: draftCount, hint: 'в работе' },
    ...(state?.revenue ? [
      { label: 'Доступно к выплате', value: formatMoney(state.revenue.summary.available_amount, currency), hint: 'можно запросить' },
      { label: 'Заявки на выплаты', value: state.revenue.summary.payout_requests_count, hint: `${state.revenue.summary.pending_payout_requests_count} ожидают` },
    ] : []),
  ];

  const actionCards = [
    state?.profile
      ? {
        title: 'Создать продукт',
        description: 'Соберите программу, видео или набор для продажи.',
        href: '/trainer/dashboard/products',
        label: 'Создать продукт',
      }
      : {
        title: 'Заполнить профиль',
        description: 'Публичная карточка нужна для продаж и доверия учеников.',
        href: '/trainer/onboarding',
        label: 'Заполнить профиль',
      },
    {
      title: 'Проверить продажи',
      description: 'Посмотрите заказы, оплаты и доступы учеников.',
      href: '/trainer/dashboard/sales',
      label: 'Продажи',
    },
    {
      title: 'Запросить выплату',
      description: 'Проверьте доступный баланс и историю заявок.',
      href: '/trainer/dashboard/payouts',
      label: 'Выплаты',
    },
    {
      title: 'Посмотреть аналитику',
      description: 'Оцените просмотры, продажи и качество данных.',
      href: '/trainer/dashboard/analytics',
      label: 'Аналитика',
    },
  ];

  return (
    <ProtectedPage title="Кабинет тренера" description="Главная сводка по продажам, ученикам, контенту и выплатам.">
      <TrainerDashboardShell
        title="Кабинет тренера"
        description="Главная сводка по продажам, ученикам, контенту и выплатам"
      >
        <div className="trainer-home-workbench">
          <section className="trainer-home-hero">
            <div>
              <span className="trainer-home-eyebrow">Главный пульт</span>
              <h2>Кабинет тренера</h2>
              <p>Главная сводка по продажам, ученикам, контенту и выплатам</p>
              <div className="trainer-home-actions">
                <Link href="/trainer/dashboard/products" className="premium-primary-button">Создать продукт</Link>
                <Link href="/trainer/videos?intent=upload" className="premium-secondary-button">Загрузить видео</Link>
                <Link href="/trainer/business" className="premium-secondary-button">Открыть бизнес</Link>
              </div>
            </div>
            <div className="trainer-home-hero-total">
              <span>{state?.revenue?.summary.available_amount ? 'Доступно к выплате' : grossRevenue > 0 ? 'Оборот' : 'Готовность профиля'}</span>
              <strong>{mainValue}</strong>
              <small>
                {state?.orders.length || 0} заказов · {state?.payments.length || 0} оплат · {publishedCount} опубликовано · {formatPercent(profileProgress)}
              </small>
            </div>
          </section>

          {user?.active_role !== 'trainer' ? (
            <section className="trainer-home-alert">
              <h3>Роль тренера ещё не активна</h3>
              <p>После одобрения заявки кабинет откроется полностью.</p>
              <Link className="premium-secondary-button" href="/trainer/application-status">Смотреть статус проверки</Link>
            </section>
          ) : null}

          {loading ? (
            <section className="trainer-home-panel">
              <h3>Загружаем кабинет тренера</h3>
              <p>Собираем продажи, оплаты, контент и профиль.</p>
            </section>
          ) : null}

          {error ? (
            <section className="trainer-home-alert">
              <h3>Не удалось загрузить кабинет тренера</h3>
              <p>{error}</p>
              <button className="premium-secondary-button" type="button" onClick={() => void load()}>
                Повторить
              </button>
            </section>
          ) : null}

          <section className="trainer-home-kpi-grid">
            {kpis.map((metric) => (
              <article className="trainer-home-kpi-card" key={metric.label}>
                <span>{metric.label}</span>
                <strong>{metric.value}</strong>
                <small>{metric.hint}</small>
              </article>
            ))}
          </section>

          {state ? (
            <section className="trainer-home-layout">
              <main className="trainer-home-main">
                <section className="trainer-home-panel">
                  <h3>Что сделать дальше</h3>
                  <div className="trainer-home-action-grid">
                    {actionCards.map((card) => (
                      <article className="trainer-home-action-card" key={card.title}>
                        <strong>{card.title}</strong>
                        <p>{card.description}</p>
                        <Link className="premium-secondary-button" href={card.href}>{card.label}</Link>
                      </article>
                    ))}
                  </div>
                </section>

                <section className="trainer-home-panel">
                  <h3>Динамика выручки</h3>
                  <div className="trainer-home-timeline">
                    {(state.revenue?.revenue_series || []).slice(-8).map((point) => (
                      <article className="trainer-home-timeline-item" key={point.date}>
                        <span>{point.date}</span>
                        <strong>{formatMoney(point.accrual_amount, currency)}</strong>
                        <small>{point.orders_count} заказов</small>
                      </article>
                    ))}
                    {!(state.revenue?.revenue_series || []).length ? (
                      <div className="trainer-home-empty">Выручка появится после первых оплаченных заказов.</div>
                    ) : null}
                  </div>
                </section>

                <section className="trainer-home-panel">
                  <h3>Лучшие продукты</h3>
                  <div className="trainer-home-product-rail">
                    {(state.revenue?.top_products || []).map((item) => (
                      <article className="trainer-home-product-card" key={`${item.item_type}-${item.title}`}>
                        <span>{trainerProductTypeLabel(item.item_type)}</span>
                        <strong>{item.title}</strong>
                        <small>{item.orders_count} заказов · {formatMoney(item.revenue, currency)}</small>
                      </article>
                    ))}
                    {!(state.revenue?.top_products || []).length ? (
                      <div className="trainer-home-empty">После первых продаж здесь появятся продукты с лучшей выручкой.</div>
                    ) : null}
                  </div>
                </section>
              </main>

              <aside className="trainer-home-sidebar">
                <section className="trainer-home-panel">
                  <h3>Профиль и доступ</h3>
                  {state.profile ? (
                    <article className="trainer-home-profile-card">
                      <span>Профиль активен</span>
                      <strong>{shortText(state.profile.display_name, 'Тренер')}</strong>
                      <small>{state.profile.slug ? `/${state.profile.slug}` : 'Публичный адрес не указан'}</small>
                      <p>{shortText(state.profile.headline)}</p>
                      <p>{shortText(state.profile.bio)}</p>
                      <Link className="premium-secondary-button" href="/trainer/onboarding">Редактировать профиль</Link>
                    </article>
                  ) : (
                    <article className="trainer-home-profile-card">
                      <strong>Профиль ещё не заполнен</strong>
                      <p>Заполните публичную карточку, чтобы ученики понимали вашу специализацию.</p>
                      <Link className="premium-primary-button" href="/trainer/onboarding">Заполнить профиль</Link>
                    </article>
                  )}
                </section>

                <section className="trainer-home-panel">
                  <h3>Быстрые действия</h3>
                  <div className="trainer-home-action-grid">
                    <Link className="premium-secondary-button" href="/trainer/videos?intent=upload">Загрузить видео</Link>
                    <Link className="premium-secondary-button" href="/trainer/dashboard/products">Продукты</Link>
                    <Link className="premium-secondary-button" href="/trainer/reviews">Отзывы</Link>
                    <Link className="premium-secondary-button" href="/trainer/business">Бизнес</Link>
                  </div>
                </section>

                <section className="trainer-home-panel">
                  <h3>Состояние кабинета</h3>
                  <div className="trainer-home-timeline">
                    <article className="trainer-home-timeline-item">
                      <span>Профиль</span>
                      <strong>{formatPercent(profileProgress)}</strong>
                      <small>{state.profile ? 'готов к продажам' : 'нужно заполнить'}</small>
                    </article>
                    <article className="trainer-home-timeline-item">
                      <span>Контент</span>
                      <strong>{publishedCount} опубликовано</strong>
                      <small>{draftCount} черновиков</small>
                    </article>
                    <article className="trainer-home-timeline-item">
                      <span>Финансы</span>
                      <strong>{state.revenue ? formatMoney(state.revenue.summary.available_amount, currency) : 'Нет данных'}</strong>
                      <small>доступно к выплате</small>
                    </article>
                  </div>
                </section>
              </aside>
            </section>
          ) : null}
        </div>
      </TrainerDashboardShell>
    </ProtectedPage>
  );
}
