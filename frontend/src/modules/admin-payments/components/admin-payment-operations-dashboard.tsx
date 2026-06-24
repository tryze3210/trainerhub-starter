'use client';

import Link from 'next/link';
import type { ReactNode } from 'react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuthSession } from '@/components/auth-provider';
import {
  adminPaymentsApi,
  type AdminPayment,
  type AdminPaymentFilters,
  type AdminPaymentRefundOperation,
  type AdminPaymentWebhookEvent,
  type AdminWebhookFilters,
  type PaymentReconciliationIssue,
  type PaymentReconciliationReport,
} from '@/modules/admin-payments/api';

type DashboardState = {
  payments: AdminPayment[];
  webhooks: AdminPaymentWebhookEvent[];
  reconciliation: PaymentReconciliationReport | null;
};

type RefundRow = AdminPaymentRefundOperation & {
  payment_id: string;
  order_id: string;
  buyer_email?: string;
  currency: string;
};

const PAYMENT_STATUSES = ['', 'succeeded', 'pending', 'failed', 'refunded', 'cancelled', 'disputed', 'charged_back'];
const WEBHOOK_STATUSES = ['', 'failed', 'rejected', 'received', 'processed', 'duplicate', 'ignored'];

function formatDate(value?: string | null) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('ru-RU');
}

function money(value?: string | number | null, currency = 'RUB') {
  if (value === undefined || value === null || value === '') return `0 ${currency}`;
  return `${value} ${currency}`;
}

function shortId(value?: string | null) {
  if (!value) return '-';
  return value.length > 12 ? `${value.slice(0, 8)}...${value.slice(-4)}` : value;
}

function statusLabel(value?: string | null) {
  return value ? value.replaceAll('_', ' ') : '-';
}

function countBy<T>(items: T[], getKey: (item: T) => string | undefined | null) {
  return items.reduce<Record<string, number>>((acc, item) => {
    const key = getKey(item) || 'unknown';
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});
}

function flattenRefunds(payments: AdminPayment[]): RefundRow[] {
  return payments.flatMap((payment) =>
    (payment.refund_operations || []).map((refund) => ({
      ...refund,
      payment_id: payment.id,
      order_id: payment.order_id,
      buyer_email: payment.buyer_email,
      currency: payment.currency,
    }))
  );
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

function Badge({ children }: { children: ReactNode }) {
  return <span className="badge secondary">{children}</span>;
}

function IssueList({ issues }: { issues: PaymentReconciliationIssue[] }) {
  if (!issues.length) {
    return <p className="muted">Payment reconciliation issues не найдены.</p>;
  }

  return (
    <div className="stack" style={{ gap: 10 }}>
      {issues.slice(0, 8).map((issue) => (
        <div className="list-item" key={`${issue.code}:${issue.entity_type}:${issue.entity_id}`}>
          <div className="row" style={{ gap: 12, alignItems: 'flex-start' }}>
            <div className="stack" style={{ gap: 6 }}>
              <div className="inline" style={{ gap: 8, flexWrap: 'wrap' }}>
                <Badge>{issue.severity}</Badge>
                <Badge>{issue.code}</Badge>
                <Badge>{issue.entity_type}</Badge>
              </div>
              <strong>{issue.message}</strong>
              <span className="muted">{issue.suggested_action}</span>
            </div>
            <Link href={`/admin/entities/${issue.entity_type}/${issue.entity_id}`} className="button secondary sm">
              Entity
            </Link>
          </div>
        </div>
      ))}
    </div>
  );
}

function RefundsTable({ refunds }: { refunds: RefundRow[] }) {
  if (!refunds.length) {
    return <p className="muted">Refund operations пока нет.</p>;
  }

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>Refund</th>
            <th>Payment</th>
            <th>Buyer</th>
            <th>Amount</th>
            <th>Status</th>
            <th>Reason</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {refunds.slice(0, 20).map((refund, index) => (
            <tr key={`${refund.payment_id}:${refund.refund_id || index}`}>
              <td>{shortId(refund.refund_id || String(index + 1))}</td>
              <td>
                <Link href={`/admin/entities/payment/${refund.payment_id}`}>{shortId(refund.payment_id)}</Link>
              </td>
              <td>{refund.buyer_email || '-'}</td>
              <td>{money(refund.amount, refund.currency)}</td>
              <td>{statusLabel(refund.status || refund.type)}</td>
              <td>{String(refund.reason || '-')}</td>
              <td>{formatDate(refund.completed_at || refund.requested_at || refund.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PaymentsTable({ payments }: { payments: AdminPayment[] }) {
  if (!payments.length) {
    return <p className="muted">Payments по текущему фильтру не найдены.</p>;
  }

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>Payment</th>
            <th>Buyer</th>
            <th>Status</th>
            <th>Amount</th>
            <th>Order</th>
            <th>Entitlement</th>
            <th>Refunds</th>
            <th>Updated</th>
          </tr>
        </thead>
        <tbody>
          {payments.map((payment) => (
            <tr key={payment.id}>
              <td>
                <div className="stack" style={{ gap: 4 }}>
                  <Link href={`/admin/entities/payment/${payment.id}`}>{shortId(payment.id)}</Link>
                  <span className="muted">{payment.provider} · {shortId(payment.external_payment_id)}</span>
                </div>
              </td>
              <td>{payment.buyer_email || '-'}</td>
              <td><Badge>{payment.status}</Badge></td>
              <td>{money(payment.amount, payment.currency)}</td>
              <td>
                <div className="stack" style={{ gap: 4 }}>
                  <Link href={`/admin/entities/order/${payment.order_id}`}>{shortId(payment.order_id)}</Link>
                  <span className="muted">{statusLabel(payment.order_status)} · {statusLabel(payment.order_type)}</span>
                </div>
              </td>
              <td>
                <div className="stack" style={{ gap: 4 }}>
                  <Badge>{payment.entitlement_summary?.status || 'unknown'}</Badge>
                  <span className="muted">
                    {payment.entitlement_summary?.active || 0} active / {payment.entitlement_summary?.total || 0} total
                  </span>
                </div>
              </td>
              <td>{payment.refund_operations?.length || 0}</td>
              <td>{formatDate(payment.updated_at || payment.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function WebhooksTable({
  webhooks,
  onReprocess,
  busyWebhookId,
}: {
  webhooks: AdminPaymentWebhookEvent[];
  onReprocess: (webhook: AdminPaymentWebhookEvent) => void;
  busyWebhookId: string;
}) {
  if (!webhooks.length) {
    return <p className="muted">Webhook events по текущему фильтру не найдены.</p>;
  }

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>Webhook</th>
            <th>Provider</th>
            <th>Event</th>
            <th>Status</th>
            <th>Payment</th>
            <th>Attempts</th>
            <th>Received</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {webhooks.map((webhook) => (
            <tr key={webhook.id}>
              <td>
                <div className="stack" style={{ gap: 4 }}>
                  <Link href={`/admin/entities/payment_webhook/${webhook.id}`}>{shortId(webhook.id)}</Link>
                  <span className="muted">{shortId(webhook.external_event_id)}</span>
                </div>
              </td>
              <td>{webhook.provider}</td>
              <td>{webhook.event_type}</td>
              <td><Badge>{webhook.status}</Badge></td>
              <td>{webhook.payment_id ? <Link href={`/admin/entities/payment/${webhook.payment_id}`}>{shortId(webhook.payment_id)}</Link> : '-'}</td>
              <td>{webhook.attempts}</td>
              <td>{formatDate(webhook.received_at || webhook.created_at)}</td>
              <td>
                <button
                  type="button"
                  className="button secondary sm"
                  disabled={busyWebhookId === webhook.id}
                  onClick={() => onReprocess(webhook)}
                >
                  {busyWebhookId === webhook.id ? '...' : 'Reprocess'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function AdminPaymentOperationsDashboard() {
  const { user } = useAuthSession();
  const isAdmin = user?.active_role === 'admin';
  const [paymentFilters, setPaymentFilters] = useState<AdminPaymentFilters>({ limit: 100 });
  const [webhookFilters, setWebhookFilters] = useState<AdminWebhookFilters>({ status: '', limit: 100 });
  const [state, setState] = useState<DashboardState>({ payments: [], webhooks: [], reconciliation: null });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [busyWebhookId, setBusyWebhookId] = useState('');

  const load = useCallback(async () => {
    if (!isAdmin) return;
    setLoading(true);
    setMessage('');
    try {
      const [payments, webhooks, reconciliation] = await Promise.all([
        adminPaymentsApi.listPayments(paymentFilters),
        adminPaymentsApi.listWebhookEvents(webhookFilters),
        adminPaymentsApi.getPaymentReconciliation(100).catch(() => null),
      ]);
      setState({ payments, webhooks, reconciliation });
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Не удалось загрузить payment admin data');
    } finally {
      setLoading(false);
    }
  }, [isAdmin, paymentFilters, webhookFilters]);

  useEffect(() => {
    void load();
  }, [load]);

  const paymentBuckets = useMemo(() => countBy(state.payments, (payment) => payment.status), [state.payments]);
  const webhookBuckets = useMemo(() => countBy(state.webhooks, (webhook) => webhook.status), [state.webhooks]);
  const refunds = useMemo(() => flattenRefunds(state.payments), [state.payments]);
  const entitlementBuckets = useMemo(
    () => countBy(state.payments, (payment) => payment.entitlement_summary?.status),
    [state.payments]
  );

  async function reprocess(webhook: AdminPaymentWebhookEvent) {
    setBusyWebhookId(webhook.id);
    setMessage('');
    try {
      await adminPaymentsApi.reprocessWebhook(webhook.id, webhook.status === 'processed');
      setMessage(`Webhook ${shortId(webhook.id)} отправлен на reprocess.`);
      await load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Не удалось reprocess webhook');
    } finally {
      setBusyWebhookId('');
    }
  }

  return (
    <section className="stack" style={{ gap: 24 }}>
      {!isAdmin ? <div className="card error">У текущей сессии нет admin-role.</div> : null}

      {message ? <div className="card">{message}</div> : null}

      <div className="grid-4">
        <StatCard title="Payments" value={state.payments.length} hint={`${paymentBuckets.succeeded || 0} succeeded`} />
        <StatCard title="Refund operations" value={refunds.length} hint={`${paymentBuckets.refunded || 0} refunded payments`} />
        <StatCard title="Webhook issues" value={(webhookBuckets.failed || 0) + (webhookBuckets.rejected || 0)} hint={`${state.webhooks.length} loaded`} />
        <StatCard
          title="Reconciliation"
          value={state.reconciliation?.status || '-'}
          hint={`${state.reconciliation?.summary.total_issues || 0} issues`}
        />
      </div>

      <div className="card">
        <div className="row" style={{ gap: 16, alignItems: 'flex-end' }}>
          <div className="stack" style={{ gap: 8 }}>
            <span className="badge secondary">Payments</span>
            <h2 className="title-md">Payment ledger</h2>
          </div>
          <div className="inline" style={{ gap: 10, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
            <select
              className="input"
              value={paymentFilters.status || ''}
              onChange={(event) => setPaymentFilters((prev) => ({ ...prev, status: event.target.value }))}
              aria-label="Payment status"
            >
              {PAYMENT_STATUSES.map((status) => (
                <option key={status || 'all'} value={status}>{status || 'all statuses'}</option>
              ))}
            </select>
            <input
              className="input"
              value={paymentFilters.provider || ''}
              onChange={(event) => setPaymentFilters((prev) => ({ ...prev, provider: event.target.value }))}
              placeholder="provider"
            />
            <input
              className="input"
              value={paymentFilters.buyer_email || ''}
              onChange={(event) => setPaymentFilters((prev) => ({ ...prev, buyer_email: event.target.value }))}
              placeholder="buyer email"
            />
            <button type="button" className="button secondary" onClick={() => void load()} disabled={loading}>
              {loading ? 'Loading...' : 'Refresh'}
            </button>
          </div>
        </div>
        <div style={{ marginTop: 18 }}>
          <PaymentsTable payments={state.payments} />
        </div>
      </div>

      <div className="grid-3">
        <div className="card">
          <h2 className="title-md">Entitlement status</h2>
          <div className="stack" style={{ gap: 10, marginTop: 16 }}>
            {Object.entries(entitlementBuckets).map(([status, count]) => (
              <div className="list-item" key={status}>
                <span className="muted">{statusLabel(status)}</span>
                <strong>{count}</strong>
              </div>
            ))}
          </div>
        </div>
        <div className="card">
          <h2 className="title-md">Payment statuses</h2>
          <div className="stack" style={{ gap: 10, marginTop: 16 }}>
            {Object.entries(paymentBuckets).map(([status, count]) => (
              <div className="list-item" key={status}>
                <span className="muted">{statusLabel(status)}</span>
                <strong>{count}</strong>
              </div>
            ))}
          </div>
        </div>
        <div className="card">
          <h2 className="title-md">Webhook statuses</h2>
          <div className="stack" style={{ gap: 10, marginTop: 16 }}>
            {Object.entries(webhookBuckets).map(([status, count]) => (
              <div className="list-item" key={status}>
                <span className="muted">{statusLabel(status)}</span>
                <strong>{count}</strong>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="row" style={{ gap: 16, alignItems: 'flex-end' }}>
          <div className="stack" style={{ gap: 8 }}>
            <span className="badge secondary">Webhook events</span>
            <h2 className="title-md">Provider event intake</h2>
          </div>
          <div className="inline" style={{ gap: 10, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
            <select
              className="input"
              value={webhookFilters.status || ''}
              onChange={(event) => setWebhookFilters((prev) => ({ ...prev, status: event.target.value }))}
              aria-label="Webhook status"
            >
              {WEBHOOK_STATUSES.map((status) => (
                <option key={status || 'all'} value={status}>{status || 'all statuses'}</option>
              ))}
            </select>
            <input
              className="input"
              value={webhookFilters.provider || ''}
              onChange={(event) => setWebhookFilters((prev) => ({ ...prev, provider: event.target.value }))}
              placeholder="provider"
            />
            <input
              className="input"
              value={webhookFilters.event_type || ''}
              onChange={(event) => setWebhookFilters((prev) => ({ ...prev, event_type: event.target.value }))}
              placeholder="event type"
            />
          </div>
        </div>
        <div style={{ marginTop: 18 }}>
          <WebhooksTable webhooks={state.webhooks} onReprocess={reprocess} busyWebhookId={busyWebhookId} />
        </div>
      </div>

      <div className="card">
        <div className="stack" style={{ gap: 8, marginBottom: 18 }}>
          <span className="badge secondary">Refunds</span>
          <h2 className="title-md">Refund operations</h2>
        </div>
        <RefundsTable refunds={refunds} />
      </div>

      <div className="card">
        <div className="row" style={{ gap: 12, alignItems: 'flex-start', marginBottom: 18 }}>
          <div className="stack" style={{ gap: 8 }}>
            <span className="badge secondary">Reconciliation issues</span>
            <h2 className="title-md">Provider payments, internal payments, entitlements</h2>
            <p className="muted">Generated: {formatDate(state.reconciliation?.generated_at)}</p>
          </div>
          <Badge>{state.reconciliation?.summary.critical_count || 0} critical</Badge>
        </div>
        <IssueList issues={state.reconciliation?.issues || []} />
      </div>
    </section>
  );
}
