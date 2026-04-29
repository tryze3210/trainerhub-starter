'use client';

import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { checkoutApi, onboardingApi, paymentsApi, privateApi, trainersApi } from '@/lib/api';
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

        {loading ? <div className="card"><p className="muted">Загружаем dashboard…</p></div> : null}
        {error ? <div className="card error">{error}</div> : null}

        {state ? (
          <>
            <div className="grid-4">
              <div className="card"><div className="kpi"><span className="muted">Onboarding</span><strong>{state.onboarding?.summary.completion_percent || 0}%</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Заказы</span><strong>{state.orders.length}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Платежи</span><strong>{state.payments.length}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Оборот</span><strong>{grossRevenue.toFixed(2)} RUB</strong></div></div>
            </div>

            <div className="grid-4">
              <div className="card"><div className="kpi"><span className="muted">Revenue 30d</span><strong>{formatMoney(state.revenue?.summary.revenue_last_30_days, currency)}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Available balance</span><strong>{formatMoney(state.revenue?.summary.available_amount, currency)}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Reserved</span><strong>{formatMoney(state.revenue?.summary.reserved_amount, currency)}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Avg order</span><strong>{formatMoney(state.revenue?.summary.avg_order_value, currency)}</strong></div></div>
            </div>

            <div className="grid-2">
              <div className="card">
                <div className="stack" style={{ gap: 12 }}>
                  <div className="row">
                    <h2 className="title-md" style={{ margin: 0 }}>Профиль тренера</h2>
                    <span className={`badge ${state.profile ? 'success' : 'warning'}`}>
                      {state.profile ? 'configured' : 'missing'}
                    </span>
                  </div>
                  {state.profile ? (
                    <>
                      <p><strong>{state.profile.display_name}</strong></p>
                      <p className="muted">slug: {state.profile.slug}</p>
                      <p>{state.profile.headline || 'Headline не заполнен.'}</p>
                      <p>{state.profile.bio || 'Bio не заполнено.'}</p>
                    </>
                  ) : (
                    <p className="muted">Профиль тренера ещё не создан. Заверши onboarding.</p>
                  )}
                </div>
              </div>

              <div className="card">
                <div className="stack" style={{ gap: 12 }}>
                  <div className="row">
                    <h2 className="title-md" style={{ margin: 0 }}>CMS summary</h2>
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
            </div>

            <div className="grid-2">
              <div className="card">
                <h2 className="title-md">Revenue last 30 days</h2>
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {(state.revenue?.revenue_series || []).slice(-8).map((point) => (
                    <div className="list-item" key={point.date}>
                      <span className="muted">{point.date}</span>
                      <strong>{point.accrual_amount} {currency}</strong>
                      <small>orders {point.orders_count}</small>
                    </div>
                  ))}
                </div>
              </div>
              <div className="card">
                <h2 className="title-md">Top products</h2>
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {(state.revenue?.top_products || []).length === 0 ? (
                    <p className="muted">Пока нет оплаченных товаров для построения рейтинга.</p>
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
              </div>
            </div>
          </>
        ) : null}
      </TrainerDashboardShell>
    </ProtectedPage>
  );
}
