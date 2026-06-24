'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { customerBillingApi } from '@/modules/customer-billing/api';
import type { CustomerBillingSnapshot } from '@/modules/customer-billing/api';
import type { Entitlement, Order, Payment, Subscription } from '@/types/api';

type InvoiceRow = {
  id: string;
  order: Order;
  payment?: Payment;
  status: string;
  amount: string;
  currency: string;
  issued_at?: string | null;
};

function formatDate(value?: string | null) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function money(value?: string | number | null, currency = 'RUB') {
  if (value === undefined || value === null || value === '') return `0 ${currency}`;
  return `${value} ${currency}`;
}

function shortId(value?: string | null) {
  if (!value) return '-';
  return value.length > 14 ? `${value.slice(0, 8)}...${value.slice(-4)}` : value;
}

function statusText(value?: string | null) {
  return value ? value.replaceAll('_', ' ') : '-';
}

function titleFromOrder(order: Order) {
  return order.title || order.items?.[0]?.title_snapshot || order.order_type || 'Покупка';
}

function titleFromSubscription(item: Subscription) {
  return item.plan?.title || item.plan_name || item.title || item.product_title || 'Подписка';
}

function titleFromEntitlement(item: Entitlement) {
  return item.content_title || item.title || item.product_title || item.target_type || item.kind || 'Доступ';
}

function entitlementStatus(item: Entitlement) {
  return item.status || item.access_status || (item.is_active ? 'active' : 'inactive');
}

function isActiveEntitlement(item: Entitlement) {
  const status = entitlementStatus(item).toLowerCase();
  if (status === 'active' || status === 'granted') return true;
  return Boolean(item.is_active);
}

function paymentForOrder(payments: Payment[], orderId?: string) {
  if (!orderId) return undefined;
  return payments.find((payment) => payment.order_id === orderId);
}

function buildInvoices(snapshot: CustomerBillingSnapshot): InvoiceRow[] {
  return snapshot.orders
    .filter((order) => ['paid', 'completed', 'refunded'].includes((order.status || '').toLowerCase()))
    .map((order) => {
      const payment = paymentForOrder(snapshot.payments, order.id);
      return {
        id: `invoice-${order.id}`,
        order,
        payment,
        status: payment?.status || order.status || 'issued',
        amount: order.total_amount || order.gross_amount || order.amount || payment?.amount || '0',
        currency: order.currency || payment?.currency || 'RUB',
        issued_at: order.paid_at || order.completed_at || payment?.confirmed_at || order.created_at,
      };
    });
}

function StatCard({ title, value, hint }: { title: string; value: string | number; hint?: string }) {
  return (
    <div className="card">
      <div className="kpi">
        <span className="muted">{title}</span>
        <strong>{value}</strong>
        {hint ? <small className="muted">{hint}</small> : null}
      </div>
    </div>
  );
}

function OrdersTable({ orders, payments }: { orders: Order[]; payments: Payment[] }) {
  if (!orders.length) return <p className="muted">Покупок пока нет.</p>;

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>Покупка</th>
            <th>Статус</th>
            <th>Сумма</th>
            <th>Платёж</th>
            <th>Дата</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((order) => {
            const payment = paymentForOrder(payments, order.id);
            return (
              <tr key={order.id}>
                <td>
                  <div className="stack" style={{ gap: 4 }}>
                    <Link href={`/orders/${order.id}`}>{titleFromOrder(order)}</Link>
                    <span className="muted">{shortId(order.id)} · {statusText(order.order_type)}</span>
                  </div>
                </td>
                <td><span className="badge secondary">{statusText(order.status)}</span></td>
                <td>{money(order.total_amount || order.gross_amount || order.amount, order.currency || 'RUB')}</td>
                <td>{payment ? <Link href={`/payments/${payment.id}`}>{statusText(payment.status)}</Link> : '-'}</td>
                <td>{formatDate(order.paid_at || order.completed_at || order.created_at || order.createdAt)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function SubscriptionsTable({ subscriptions }: { subscriptions: Subscription[] }) {
  if (!subscriptions.length) return <p className="muted">Подписок пока нет.</p>;

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>Подписка</th>
            <th>Статус</th>
            <th>Период</th>
            <th>Сумма</th>
            <th>Автопродление</th>
          </tr>
        </thead>
        <tbody>
          {subscriptions.map((item) => (
            <tr key={item.id}>
              <td>
                <div className="stack" style={{ gap: 4 }}>
                  <Link href="/subscriptions">{titleFromSubscription(item)}</Link>
                  <span className="muted">{shortId(item.id)}</span>
                </div>
              </td>
              <td><span className="badge secondary">{statusText(item.status)}</span></td>
              <td>{formatDate(item.starts_at || item.started_at)} / {formatDate(item.ends_at || item.current_period_end)}</td>
              <td>{money(item.amount || item.price_amount || item.plan?.price, item.currency || item.plan?.currency || 'RUB')}</td>
              <td>{item.auto_renew ? 'Включено' : 'Выключено'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PaymentsTable({ payments }: { payments: Payment[] }) {
  if (!payments.length) return <p className="muted">Платежей пока нет.</p>;

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>Платёж</th>
            <th>Provider</th>
            <th>Статус</th>
            <th>Сумма</th>
            <th>Дата</th>
          </tr>
        </thead>
        <tbody>
          {payments.map((payment) => (
            <tr key={payment.id}>
              <td><Link href={`/payments/${payment.id}`}>{shortId(payment.id)}</Link></td>
              <td>{payment.provider || '-'}</td>
              <td><span className="badge secondary">{statusText(payment.status)}</span></td>
              <td>{money(payment.amount || payment.gross_amount, payment.currency || 'RUB')}</td>
              <td>{formatDate(payment.confirmed_at || payment.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function InvoicesTable({ invoices }: { invoices: InvoiceRow[] }) {
  if (!invoices.length) return <p className="muted">Чеков и инвойсов пока нет.</p>;

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>Документ</th>
            <th>Покупка</th>
            <th>Статус</th>
            <th>Сумма</th>
            <th>Дата</th>
          </tr>
        </thead>
        <tbody>
          {invoices.map((invoice) => (
            <tr key={invoice.id}>
              <td>{shortId(invoice.id)}</td>
              <td><Link href={`/orders/${invoice.order.id}`}>{titleFromOrder(invoice.order)}</Link></td>
              <td><span className="badge secondary">{statusText(invoice.status)}</span></td>
              <td>{money(invoice.amount, invoice.currency)}</td>
              <td>{formatDate(invoice.issued_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EntitlementsGrid({ entitlements }: { entitlements: Entitlement[] }) {
  const active = entitlements.filter(isActiveEntitlement);
  if (!active.length) return <p className="muted">Активных доступов пока нет.</p>;

  return (
    <div className="grid-2">
      {active.slice(0, 8).map((item) => (
        <article className="card compact" key={item.id}>
          <div className="stack" style={{ gap: 10 }}>
            <div className="row">
              <strong>{titleFromEntitlement(item)}</strong>
              <span className="badge success">{statusText(entitlementStatus(item))}</span>
            </div>
            <div className="grid-2">
              <div className="list-item"><span className="muted">Тип</span><strong>{statusText(item.target_type || item.kind)}</strong></div>
              <div className="list-item"><span className="muted">Истекает</span><strong>{formatDate(item.ends_at || item.expires_at)}</strong></div>
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}

export default function BillingPage() {
  const { isAuthenticated, isLoading: sessionLoading } = useAuthSession();
  const [snapshot, setSnapshot] = useState<CustomerBillingSnapshot>({
    orders: [],
    payments: [],
    subscriptions: [],
    entitlements: [],
  });
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  async function load() {
    try {
      setLoading(true);
      setMessage('');
      setSnapshot(await customerBillingApi.getSnapshot());
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Не удалось загрузить billing center');
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

  const invoices = useMemo(() => buildInvoices(snapshot), [snapshot]);
  const activeEntitlements = useMemo(() => snapshot.entitlements.filter(isActiveEntitlement), [snapshot.entitlements]);
  const failedPayments = useMemo(
    () => snapshot.payments.filter((payment) => ['failed', 'cancelled', 'disputed', 'charged_back'].includes((payment.status || '').toLowerCase())),
    [snapshot.payments]
  );
  const totalSpend = useMemo(
    () => snapshot.orders.reduce((sum, order) => sum + Number(order.total_amount || order.gross_amount || order.amount || 0), 0),
    [snapshot.orders]
  );

  return (
    <ProtectedPage title="Billing" description="Покупки, подписки, платежи, чеки и активные доступы клиента.">
      <section className="stack" style={{ gap: 24 }}>
        <div className="row" style={{ alignItems: 'flex-start' }}>
          <div className="stack" style={{ gap: 10 }}>
            <span className="badge secondary">Customer billing</span>
            <h1>Billing</h1>
            <p className="lead">Единый кабинет для покупок, подписок, чеков, платежных статусов и активных доступов.</p>
          </div>
          <div className="inline">
            <button className="button secondary" type="button" onClick={() => void load()} disabled={loading}>
              {loading ? 'Загрузка...' : 'Обновить'}
            </button>
            <Link href="/customer/hub" className="button ghost">Customer hub</Link>
          </div>
        </div>

        <div className="grid-4">
          <StatCard title="Покупки" value={snapshot.orders.length} hint={`${totalSpend.toFixed(2)} RUB`} />
          <StatCard title="Подписки" value={snapshot.subscriptions.length} hint={`${snapshot.subscriptions.filter((item) => item.status === 'active').length} active`} />
          <StatCard title="Платежи" value={snapshot.payments.length} hint={`${failedPayments.length} need attention`} />
          <StatCard title="Активные доступы" value={activeEntitlements.length} hint={`${snapshot.entitlements.length} total`} />
        </div>

        {message ? <div className="card error">{message}</div> : null}
        {loading ? <div className="card">Загрузка billing center...</div> : null}

        {!loading ? (
          <>
            <div className="card">
              <div className="stack" style={{ gap: 8, marginBottom: 18 }}>
                <span className="badge secondary">Мои покупки</span>
                <h2 className="title-md">Orders</h2>
              </div>
              <OrdersTable orders={snapshot.orders} payments={snapshot.payments} />
            </div>

            <div className="card">
              <div className="stack" style={{ gap: 8, marginBottom: 18 }}>
                <span className="badge secondary">Мои подписки</span>
                <h2 className="title-md">Subscriptions</h2>
              </div>
              <SubscriptionsTable subscriptions={snapshot.subscriptions} />
            </div>

            <div className="card">
              <div className="stack" style={{ gap: 8, marginBottom: 18 }}>
                <span className="badge secondary">Чеки / инвойсы</span>
                <h2 className="title-md">Receipts</h2>
              </div>
              <InvoicesTable invoices={invoices} />
            </div>

            <div className="card">
              <div className="stack" style={{ gap: 8, marginBottom: 18 }}>
                <span className="badge secondary">Статусы платежей</span>
                <h2 className="title-md">Payments</h2>
              </div>
              <PaymentsTable payments={snapshot.payments} />
            </div>

            <div className="card">
              <div className="row" style={{ gap: 12, alignItems: 'flex-start', marginBottom: 18 }}>
                <div className="stack" style={{ gap: 8 }}>
                  <span className="badge secondary">Активные доступы</span>
                  <h2 className="title-md">Entitlements</h2>
                </div>
                <Link href="/entitlements" className="button secondary">Все доступы</Link>
              </div>
              <EntitlementsGrid entitlements={snapshot.entitlements} />
            </div>
          </>
        ) : null}
      </section>
    </ProtectedPage>
  );
}
