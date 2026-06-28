'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { customerBillingApi, type CustomerBillingSnapshot } from '@/modules/customer-billing/api';
import {
  CustomerCabinetShell,
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
  formatCustomerMoney,
  orderAmount,
  orderStatusLabel,
  orderTitle,
  paymentStatusLabel,
  shortCustomerNumber,
  statusTone,
  subscriptionStatusLabel,
  subscriptionTitle,
} from '@/modules/customer-cabinet/components/customer-format';
import type { Entitlement, Order, Payment } from '@/types/api';

const emptySnapshot: CustomerBillingSnapshot = {
  orders: [],
  payments: [],
  subscriptions: [],
  entitlements: [],
};

function isActiveEntitlement(item: Entitlement) {
  const status = entitlementStatus(item).toLowerCase();
  return item.is_active || status === 'active' || status === 'granted';
}

function paymentForOrder(payments: Payment[], order: Order) {
  return payments.find((payment) => payment.order_id === order.id);
}

export default function BillingPage() {
  const { isAuthenticated, isLoading: sessionLoading } = useAuthSession();
  const [snapshot, setSnapshot] = useState<CustomerBillingSnapshot>(emptySnapshot);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  async function load() {
    try {
      setLoading(true);
      setMessage('');
      setSnapshot(await customerBillingApi.getSnapshot());
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

  const activeEntitlements = useMemo(() => snapshot.entitlements.filter(isActiveEntitlement), [snapshot.entitlements]);
  const totalSpend = useMemo(() => snapshot.orders.reduce((sum, order) => sum + Number(order.total_amount || order.gross_amount || order.amount || 0), 0), [snapshot.orders]);
  const metrics: CustomerMetric[] = [
    { label: 'Покупки', value: snapshot.orders.length, hint: formatCustomerMoney(totalSpend, 'RUB'), tone: 'neutral' },
    { label: 'Подписки', value: snapshot.subscriptions.length, hint: `${snapshot.subscriptions.filter((item) => item.status === 'active').length} активных`, tone: 'success' },
    { label: 'Платежи', value: snapshot.payments.length, hint: 'История оплат', tone: 'neutral' },
    { label: 'Активные доступы', value: activeEntitlements.length, hint: 'Готовы к обучению', tone: 'success' },
  ];

  return (
    <ProtectedPage title="Финансы и документы" description="Финансовый раздел доступен только после входа.">
      <CustomerCabinetShell
        title="Финансы и документы"
        description="Покупки, платежи, подписки, чеки и активные доступы в одном разделе."
        actions={<button className="premium-secondary-button" type="button" onClick={() => void load()} disabled={loading}>Обновить</button>}
      >
        <div className="customer-metric-grid">
          {metrics.map((metric) => <CustomerMetricCard key={metric.label} metric={metric} />)}
        </div>
        {message ? <CustomerErrorState message={message} onRetry={() => void load()} /> : null}
        {loading ? <CustomerLoadingState /> : null}

        <div className="customer-billing-tabs">
          <Link href="#orders">Покупки</Link>
          <Link href="#subscriptions">Подписки</Link>
          <Link href="#documents">Чеки и документы</Link>
          <Link href="#payments">Платежи</Link>
          <Link href="#accesses">Активные доступы</Link>
        </div>

        <section id="orders" className="customer-section-card">
          <div className="customer-section-header"><h2>Покупки</h2><Link href="/orders" className="premium-secondary-button">Все заказы</Link></div>
          <div className="customer-commerce-list">
            {snapshot.orders.slice(0, 8).map((order) => {
              const payment = paymentForOrder(snapshot.payments, order);
              return (
                <article className="customer-commerce-card" key={order.id}>
                  <CustomerStatusBadge tone={statusTone(order.status)}>{orderStatusLabel(order.status)}</CustomerStatusBadge>
                  <strong>{orderTitle(order)}</strong>
                  <span>{shortCustomerNumber(order.id, 'ORD')} · {orderAmount(order)}</span>
                  {payment ? <small>Платёж: {paymentStatusLabel(payment.status)}</small> : null}
                </article>
              );
            })}
            {!snapshot.orders.length && !loading ? <CustomerEmptyState title="Покупок пока нет" description="После покупки данные появятся здесь." /> : null}
          </div>
        </section>

        <section id="subscriptions" className="customer-section-card">
          <div className="customer-section-header"><h2>Подписки</h2><Link href="/subscriptions" className="premium-secondary-button">Управлять</Link></div>
          <div className="customer-commerce-list">
            {snapshot.subscriptions.slice(0, 8).map((item) => (
              <article className="customer-commerce-card" key={item.id}>
                <CustomerStatusBadge tone={statusTone(item.status, item.is_active)}>{subscriptionStatusLabel(item.status)}</CustomerStatusBadge>
                <strong>{subscriptionTitle(item)}</strong>
                <span>{formatCustomerMoney(item.amount || item.price_amount || item.plan?.price, item.currency || item.plan?.currency || 'RUB')}</span>
              </article>
            ))}
            {!snapshot.subscriptions.length && !loading ? <CustomerEmptyState title="Подписок пока нет" description="Они появятся после оформления." /> : null}
          </div>
        </section>

        <section id="documents" className="customer-section-card">
          <div className="customer-section-header"><h2>Чеки и документы</h2></div>
          <div className="customer-commerce-list">
            {snapshot.orders.filter((order) => ['paid', 'completed', 'refunded'].includes((order.status || '').toLowerCase())).slice(0, 8).map((order) => (
              <article className="customer-commerce-card" key={`doc-${order.id}`}>
                <CustomerStatusBadge tone="success">Сформирован</CustomerStatusBadge>
                <strong>{shortCustomerNumber(order.id, 'DOC')}</strong>
                <span>{orderTitle(order)} · {orderAmount(order)}</span>
                <small>{formatCustomerDate(order.paid_at || order.completed_at || order.created_at)}</small>
              </article>
            ))}
            {!snapshot.orders.some((order) => ['paid', 'completed', 'refunded'].includes((order.status || '').toLowerCase())) && !loading ? (
              <CustomerEmptyState title="Документов пока нет" description="Чеки появятся после успешной оплаты." actionHref="/orders" actionLabel="Открыть заказы" />
            ) : null}
          </div>
        </section>

        <section id="payments" className="customer-section-card">
          <div className="customer-section-header"><h2>Платежи</h2><Link href="/payments" className="premium-secondary-button">Все платежи</Link></div>
          <div className="customer-commerce-list">
            {snapshot.payments.slice(0, 8).map((payment) => (
              <article className="customer-commerce-card" key={payment.id}>
                <CustomerStatusBadge tone={statusTone(payment.status)}>{paymentStatusLabel(payment.status)}</CustomerStatusBadge>
                <strong>{shortCustomerNumber(payment.id, 'PAY')}</strong>
                <span>{formatCustomerMoney(payment.amount || payment.gross_amount, payment.currency || 'RUB')}</span>
              </article>
            ))}
            {!snapshot.payments.length && !loading ? <CustomerEmptyState title="Платежей пока нет" description="После оплаты история появится здесь." /> : null}
          </div>
        </section>

        <section id="accesses" className="customer-section-card">
          <div className="customer-section-header"><h2>Активные доступы</h2><Link href="/entitlements" className="premium-secondary-button">Все доступы</Link></div>
          <div className="customer-access-grid">
            {activeEntitlements.slice(0, 8).map((item) => (
              <article className="customer-access-card" key={item.id}>
                <CustomerStatusBadge tone="success">Активен</CustomerStatusBadge>
                <h3>{entitlementTitle(item)}</h3>
                <p>{entitlementType(item)} · {item.trainer_name || 'TrainerHub'}</p>
              </article>
            ))}
            {!activeEntitlements.length && !loading ? <CustomerEmptyState title="Активных доступов пока нет" description="Они появятся после оплаты." /> : null}
          </div>
        </section>
      </CustomerCabinetShell>
    </ProtectedPage>
  );
}
