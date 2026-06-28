'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { authApi } from '@/lib/api';
import { customerBillingApi, type CustomerBillingSnapshot } from '@/modules/customer-billing/api';
import {
  CustomerCabinetShell,
  CustomerDashboardCard,
  CustomerEmptyState,
  CustomerErrorState,
  CustomerLoadingState,
  CustomerMetricCard,
  CustomerStatusBadge,
  type CustomerMetric,
} from '@/modules/customer-cabinet/components';
import {
  entitlementStatus,
  entitlementTitle,
  entitlementType,
  formatCustomerDate,
  orderAmount,
  orderStatusLabel,
  orderTitle,
  paymentStatusLabel,
  shortCustomerNumber,
  statusTone,
  subscriptionStatusLabel,
  subscriptionTitle,
} from '@/modules/customer-cabinet/components/customer-format';
import type { AuthUser, Order, Payment, SessionPayload } from '@/types/api';

const emptySnapshot: CustomerBillingSnapshot = {
  orders: [],
  payments: [],
  subscriptions: [],
  entitlements: [],
};

function isActiveAccess(status?: string, active?: boolean) {
  const value = (status || '').toLowerCase();
  return active || value === 'active' || value === 'granted';
}

function paymentForOrder(payments: Payment[], order: Order) {
  return payments.find((payment) => payment.order_id === order.id);
}

function nextAction(snapshot: CustomerBillingSnapshot) {
  const unpaid = snapshot.orders.find((order) => ['pending', 'awaiting_payment', 'created'].includes((order.status || '').toLowerCase()));
  if (unpaid) return { title: 'Завершить оплату', description: orderTitle(unpaid), href: `/orders/${unpaid.id}` };

  const activeAccess = snapshot.entitlements.find((item) => isActiveAccess(entitlementStatus(item), item.is_active));
  if (activeAccess) return { title: 'Продолжить обучение', description: entitlementTitle(activeAccess), href: '/learning' };

  return { title: 'Открыть каталог', description: 'Выберите программу, видеоурок или подписку.', href: '/catalog' };
}

function DashboardMetrics({ snapshot }: { snapshot: CustomerBillingSnapshot }) {
  const metrics: CustomerMetric[] = [
    {
      label: 'Активные доступы',
      value: snapshot.entitlements.filter((item) => isActiveAccess(entitlementStatus(item), item.is_active)).length,
      hint: 'Готовы к обучению',
      tone: 'success',
    },
    {
      label: 'Программы в обучении',
      value: snapshot.entitlements.filter((item) => ['program', 'course'].includes((item.target_type || item.content_type || item.kind || '').toLowerCase())).length,
      hint: 'Курсы и программы',
      tone: 'neutral',
    },
    {
      label: 'Заказы',
      value: snapshot.orders.length,
      hint: 'История покупок',
      tone: 'neutral',
    },
    {
      label: 'Непрочитанные сообщения',
      value: 'Нет данных',
      hint: 'Откройте сообщения',
      tone: 'warning',
    },
  ];

  return (
    <div className="customer-metric-grid">
      {metrics.map((metric) => <CustomerMetricCard key={metric.label} metric={metric} />)}
    </div>
  );
}

function ProfileCard({ user }: { user: AuthUser | null | undefined }) {
  return (
    <CustomerDashboardCard title="Профиль">
      <div className="customer-commerce-card">
        <strong>{user?.full_name || user?.email || 'Пользователь TrainerHub'}</strong>
        <span>{user?.email || 'Email не указан'}</span>
        <div className="customer-commerce-list">
          <div><span>Город</span><strong>{user?.city || 'Нет данных'}</strong></div>
          <div><span>Страна</span><strong>{user?.country || 'Нет данных'}</strong></div>
          <div><span>Язык</span><strong>{user?.preferred_language || 'Русский'}</strong></div>
        </div>
      </div>
    </CustomerDashboardCard>
  );
}

export default function CabinetPage() {
  const { user, isAuthenticated, isLoading: sessionLoading } = useAuthSession();
  const [session, setSession] = useState<SessionPayload | null>(null);
  const [snapshot, setSnapshot] = useState<CustomerBillingSnapshot>(emptySnapshot);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  async function load() {
    try {
      setLoading(true);
      setMessage('');
      const [sessionPayload, billingPayload] = await Promise.all([
        authApi.me(),
        customerBillingApi.getSnapshot().catch(() => emptySnapshot),
      ]);
      setSession(sessionPayload);
      setSnapshot(billingPayload);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Не удалось загрузить данные');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (sessionLoading) return;
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }
    void load();
  }, [isAuthenticated, sessionLoading]);

  const activeUser = session?.user || user;
  const isTrainer = activeUser?.active_role === 'trainer';
  const action = useMemo(() => nextAction(snapshot), [snapshot]);
  const recentOrders = snapshot.orders.slice(0, 3);
  const recentPayments = snapshot.payments.slice(0, 3);
  const activeAccesses = snapshot.entitlements.filter((item) => isActiveAccess(entitlementStatus(item), item.is_active)).slice(0, 4);
  const activeSubscriptions = snapshot.subscriptions.filter((item) => ['active', 'trial', 'pending', 'past_due'].includes((item.status || '').toLowerCase())).slice(0, 3);

  return (
    <ProtectedPage title="Личный кабинет" description="Личный кабинет доступен только авторизованным пользователям.">
      <CustomerCabinetShell
        title="Личный кабинет"
        description="Ваши программы, доступы, заказы, подписки и сообщения собраны в одном рабочем пространстве."
        actions={<button className="premium-secondary-button" type="button" onClick={() => void load()} disabled={loading}>Обновить</button>}
      >
        {message ? <CustomerErrorState message={message} onRetry={() => void load()} /> : null}
        {loading ? <CustomerLoadingState /> : null}

        {isTrainer ? (
          <CustomerDashboardCard title="Кабинет тренера">
            <div className="customer-dashboard-grid">
              <div>
                <p>Вы вошли как тренер. Управление продуктами, учениками и продажами находится в кабинете тренера.</p>
                <Link href="/trainer/dashboard" className="premium-primary-button">Открыть кабинет тренера</Link>
              </div>
            </div>
          </CustomerDashboardCard>
        ) : null}

        <section className="customer-page-hero">
          <div>
            <span className="premium-eyebrow">Следующий шаг</span>
            <h2>{action.title}</h2>
            <p>{action.description}</p>
          </div>
          <Link href={action.href} className="premium-primary-button">{action.title}</Link>
        </section>

        <DashboardMetrics snapshot={snapshot} />

        <div className="customer-dashboard-grid">
          <CustomerDashboardCard title="Продолжить обучение" action={<Link href="/learning" className="premium-secondary-button">Перейти</Link>}>
            {activeAccesses[0] ? (
              <div className="customer-access-card">
                <CustomerStatusBadge tone="success">Активен</CustomerStatusBadge>
                <h3>{entitlementTitle(activeAccesses[0])}</h3>
                <p>{entitlementType(activeAccesses[0])} · {activeAccesses[0].trainer_name || 'TrainerHub'}</p>
                <Link href="/learning" className="premium-primary-button">Продолжить</Link>
              </div>
            ) : (
              <CustomerEmptyState title="Обучение пока не начато" description="После покупки программа появится здесь." />
            )}
          </CustomerDashboardCard>

          <CustomerDashboardCard title="Активные доступы" action={<Link href="/entitlements" className="premium-secondary-button">Все доступы</Link>}>
            <div className="customer-access-grid">
              {activeAccesses.map((item) => (
                <article className="customer-access-card" key={item.id}>
                  <CustomerStatusBadge tone="success">{entitlementStatus(item) ? 'Активен' : 'Готов'}</CustomerStatusBadge>
                  <h3>{entitlementTitle(item)}</h3>
                  <p>{entitlementType(item)} · {item.trainer_name || 'TrainerHub'}</p>
                  <span>До: {formatCustomerDate(item.ends_at || item.expires_at)}</span>
                </article>
              ))}
              {!activeAccesses.length ? <CustomerEmptyState title="Активных доступов пока нет" description="Оформите покупку, чтобы начать обучение." /> : null}
            </div>
          </CustomerDashboardCard>

          <CustomerDashboardCard title="Недавние заказы и платежи" action={<Link href="/orders" className="premium-secondary-button">Все заказы</Link>}>
            <div className="customer-commerce-list">
              {recentOrders.map((order) => {
                const payment = paymentForOrder(recentPayments, order);
                return (
                  <Link href={`/orders/${order.id}`} className="customer-commerce-card" key={order.id}>
                    <CustomerStatusBadge tone={statusTone(order.status)}>{orderStatusLabel(order.status)}</CustomerStatusBadge>
                    <strong>{orderTitle(order)}</strong>
                    <span>{shortCustomerNumber(order.id, 'ORD')} · {orderAmount(order)}</span>
                    {payment ? <small>Платёж: {paymentStatusLabel(payment.status)}</small> : null}
                  </Link>
                );
              })}
              {!recentOrders.length ? <CustomerEmptyState title="Заказов пока нет" description="Ваши покупки появятся здесь после оформления." /> : null}
            </div>
          </CustomerDashboardCard>

          <CustomerDashboardCard title="Подписки" action={<Link href="/subscriptions" className="premium-secondary-button">Управлять</Link>}>
            <div className="customer-commerce-list">
              {activeSubscriptions.map((item) => (
                <Link href="/subscriptions" className="customer-commerce-card" key={item.id}>
                  <CustomerStatusBadge tone={statusTone(item.status, item.is_active)}>{subscriptionStatusLabel(item.status)}</CustomerStatusBadge>
                  <strong>{subscriptionTitle(item)}</strong>
                  <span>Период до {formatCustomerDate(item.ends_at || item.current_period_end)}</span>
                </Link>
              ))}
              {!activeSubscriptions.length ? <CustomerEmptyState title="Подписок пока нет" description="Подписки появятся после покупки." /> : null}
            </div>
          </CustomerDashboardCard>

          <CustomerDashboardCard title="Сообщения" action={<Link href="/messages" className="premium-secondary-button">Открыть</Link>}>
            <div className="customer-commerce-card">
              <strong>Диалоги с тренерами</strong>
              <span>Ответы по программам и системные уведомления находятся в разделе сообщений.</span>
              <Link href="/messages" className="premium-primary-button">Открыть сообщения</Link>
            </div>
          </CustomerDashboardCard>

          <ProfileCard user={activeUser} />
        </div>
      </CustomerCabinetShell>
    </ProtectedPage>
  );
}
