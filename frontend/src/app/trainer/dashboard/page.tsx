'use client';

import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { checkoutApi, onboardingApi, paymentsApi, privateApi, trainersApi } from '@/lib/api';
import {
  DSBarChart,
  DSEmptyState,
  DSSection,
  DSSkeleton,
  DSStatsGrid,
  DSStatusDot,
  DSTransitionPanel,
} from '@/design-system';
import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
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

  const cms = Array.isArray(cmsPayload) ? cmsPayload[0] || null : cmsPayload;

  return {
    onboarding,
    profile,
    cms,
    payments,
    orders,
    revenue,
  };
}

function formatMoney(value?: string | number, currency = 'RUB') {
  if (value === undefined || value === null || value === '') return `0 ${currency}`;
  return `${value} ${currency}`;
}

export default function TrainerDashboardPage() {
  const { user } = useAuthSession();
  const [state, setState] = useState<DashboardState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    void (async () => {
      try {
        setLoading(true);
        setError('');
        setState(await loadDashboardState());
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Не удалось загрузить dashboard');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const grossRevenue = useMemo(() => {
    return (state?.payments || []).reduce((sum, payment) => {
      const value = Number(payment.gross_amount || payment.amount || 0);
      return Number.isFinite(value) ? sum + value : sum;
    }, 0);
  }, [state]);

  const currency = state?.revenue?.summary.currency || 'RUB';

  return (
    <ProtectedPage title="Trainer dashboard" description="Dashboard тренера доступен только после авторизации.">
      <TrainerDashboardShell
        title="Trainer dashboard"
        description="Операционный dashboard тренера: onboarding, content pipeline, revenue KPIs и payout readiness."
      >
        {user?.active_role !== 'trainer' ? (
          <div className="card warning">Текущая сессия не является trainer-аккаунтом.</div>
        ) : null}

        {loading ? (
          <div className="card">
            <DSSkeleton lines={5} />
          </div>
        ) : null}
        {error ? <div className="card error">{error}</div> : null}

        {state ? (
          <DSTransitionPanel active className="stack" style={{ gap: 24 }}>
            <DSStatsGrid
              stats={[
                {
                  label: 'Onboarding',
                  value: `${state.onboarding?.summary.completion_percent || 0}%`,
                  hint: 'Profile readiness',
                  tone: (state.onboarding?.summary.completion_percent || 0) >= 100 ? 'success' : 'warning',
                },
                {
                  label: 'Заказы',
                  value: state.orders.length,
                  hint: 'All visible orders',
                  tone: 'primary',
                },
                {
                  label: 'Платежи',
                  value: state.payments.length,
                  hint: 'Payment records',
                  tone: 'primary',
                },
                {
                  label: 'Оборот',
                  value: `${grossRevenue.toFixed(2)} RUB`,
                  hint: 'Gross payment volume',
                  tone: 'success',
                },
              ]}
            />

            <DSStatsGrid
              stats={[
                {
                  label: 'Revenue 30d',
                  value: formatMoney(state.revenue?.summary.revenue_last_30_days, currency),
                  hint: 'Last 30 days',
                  tone: 'success',
                },
                {
                  label: 'Available balance',
                  value: formatMoney(state.revenue?.summary.available_amount, currency),
                  hint: 'Ready for payout',
                  tone: 'success',
                },
                {
                  label: 'Reserved',
                  value: formatMoney(state.revenue?.summary.reserved_amount, currency),
                  hint: 'Held by policy',
                  tone: 'warning',
                },
                {
                  label: 'Avg order',
                  value: formatMoney(state.revenue?.summary.avg_order_value, currency),
                  hint: 'Average paid order',
                  tone: 'primary',
                },
              ]}
            />

            <div className="grid-2">
              <DSSection title="Профиль тренера" description="Публичная карточка и storefront readiness.">
                <div className="card compact">
                  <div className="stack" style={{ gap: 12 }}>
                  <div className="row">
                    <DSStatusDot tone={state.profile ? 'success' : 'warning'} label={state.profile ? 'Configured' : 'Missing'} />
                  </div>
                  {state.profile ? (
                    <>
                      <p><strong>{state.profile.display_name}</strong></p>
                      <p className="muted">slug: {state.profile.slug}</p>
                      <p>{state.profile.headline || 'Headline не заполнен.'}</p>
                      <p>{state.profile.bio || 'Bio не заполнено.'}</p>
                    </>
                  ) : (
                    <DSEmptyState title="Профиль не создан" description="Заверши onboarding, чтобы открыть публичную карточку." />
                  )}
                  </div>
                </div>
              </DSSection>

              <DSSection title="CMS summary" description="Состояние content pipeline.">
                <div className="card compact">
                  <div className="stack" style={{ gap: 12 }}>
                  <div className="row">
                    <span className="badge secondary">trainer-cms</span>
                  </div>
                  <div className="grid-2">
                    <div className="card compact"><div className="kpi"><span className="muted">Draft videos</span><strong>{state.cms?.draft_videos_count || 0}</strong></div></div>
                    <div className="card compact"><div className="kpi"><span className="muted">Published videos</span><strong>{state.cms?.published_videos_count || 0}</strong></div></div>
                    <div className="card compact"><div className="kpi"><span className="muted">Pending review</span><strong>{state.cms?.pending_review_count || 0}</strong></div></div>
                    <div className="card compact"><div className="kpi"><span className="muted">Sales count</span><strong>{state.cms?.total_sales_count || 0}</strong></div></div>
                  </div>
                  </div>
                </div>
              </DSSection>
            </div>

            <div className="grid-2">
              <DSSection title="Revenue last 30 days" description="Последние точки revenue series.">
                <div className="card compact stack" style={{ gap: 16 }}>
                  {(state.revenue?.revenue_series || []).length > 0 ? (
                    <DSBarChart
                      label="Trainer revenue chart"
                      data={(state.revenue?.revenue_series || []).slice(-8).map((point) => ({
                        label: point.date,
                        value: Number(point.accrual_amount || 0),
                        tone: 'success',
                      }))}
                    />
                  ) : (
                    <DSEmptyState title="Revenue пока нет" description="График появится после первых оплаченных заказов." />
                  )}
                  {(state.revenue?.revenue_series || []).slice(-8).map((point) => (
                    <div className="list-item" key={point.date}>
                      <span className="muted">{point.date}</span>
                      <strong>{point.accrual_amount} {currency}</strong>
                      <small>orders {point.orders_count}</small>
                    </div>
                  ))}
                </div>
              </DSSection>
              <DSSection title="Top products" description="Товары с максимальной выручкой.">
                <div className="card compact stack" style={{ gap: 10 }}>
                  {(state.revenue?.top_products || []).length === 0 ? (
                    <DSEmptyState title="Рейтинга пока нет" description="Пока нет оплаченных товаров для построения рейтинга." />
                  ) : (
                    state.revenue?.top_products.map((item) => (
                      <div className="list-item" key={`${item.item_type}-${item.title}`}>
                        <div className="stack" style={{ gap: 2 }}>
                          <strong>{item.title}</strong>
                          <small>{item.item_type}</small>
                        </div>
                        <strong>{item.revenue} {currency}</strong>
                      </div>
                    ))
                  )}
                </div>
              </DSSection>
            </div>
          </DSTransitionPanel>
        ) : null}
      </TrainerDashboardShell>
    </ProtectedPage>
  );
}
