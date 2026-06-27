'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuthSession } from '@/components/auth-provider';
import {
  DSBadge,
  DSDataTable,
  DSEmptyState,
  DSSection,
  DSSelect,
  DSSkeleton,
  DSStatsGrid,
  DSStatusDot,
  DSTextField,
  DSTransitionPanel,
} from '@/design-system';
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

function IssueList({ issues }: { issues: PaymentReconciliationIssue[] }) {
  if (!issues.length) {
    return <DSEmptyState title="Reconciliation issues не найдены" description="Платежи, provider events и entitlements сейчас согласованы." />;
  }

  return (
    <div className="stack" style={{ gap: 10 }}>
      {issues.slice(0, 8).map((issue) => (
        <div className="list-item" key={`${issue.code}:${issue.entity_type}:${issue.entity_id}`}>
          <div className="row" style={{ gap: 12, alignItems: 'flex-start' }}>
            <div className="stack" style={{ gap: 6 }}>
              <div className="inline" style={{ gap: 8, flexWrap: 'wrap' }}>
                <DSBadge tone={issue.severity === 'critical' ? 'danger' : 'secondary'}>{issue.severity}</DSBadge>
                <DSBadge tone="secondary">{issue.code}</DSBadge>
                <DSBadge tone="secondary">{issue.entity_type}</DSBadge>
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
    return <DSEmptyState title="Refund operations пока нет" description="Возвраты появятся здесь после partial/full refund." />;
  }

  return (
    <DSDataTable
      columns={[
        { key: 'refund', label: 'Refund' },
        { key: 'payment', label: 'Payment' },
        { key: 'buyer', label: 'Buyer' },
        { key: 'amount', label: 'Amount' },
        { key: 'status', label: 'Status' },
        { key: 'reason', label: 'Reason' },
        { key: 'timestamp', label: 'Timestamp' },
      ]}
      rows={refunds.slice(0, 20).map((refund, index) => ({
        refund: shortId(refund.refund_id || String(index + 1)),
        payment: <Link href={`/admin/entities/payment/${refund.payment_id}`}>{shortId(refund.payment_id)}</Link>,
        buyer: refund.buyer_email || '-',
        amount: money(refund.amount, refund.currency),
        status: statusLabel(refund.status || refund.type),
        reason: String(refund.reason || '-'),
        timestamp: formatDate(refund.completed_at || refund.requested_at || refund.created_at),
      }))}
      getRowKey={(_, index) => `${refunds[index]?.payment_id}:${refunds[index]?.refund_id || index}`}
    />
  );
}

function PaymentsTable({ payments }: { payments: AdminPayment[] }) {
  if (!payments.length) {
    return <DSEmptyState title="Payments не найдены" description="Измени фильтры или обнови список." />;
  }

  return (
    <DSDataTable
      columns={[
        { key: 'payment', label: 'Payment' },
        { key: 'buyer', label: 'Buyer' },
        { key: 'status', label: 'Status' },
        { key: 'amount', label: 'Amount' },
        { key: 'order', label: 'Order' },
        { key: 'entitlement', label: 'Entitlement' },
        { key: 'refunds', label: 'Refunds' },
        { key: 'updated', label: 'Updated' },
      ]}
      rows={payments.map((payment) => ({
        payment: (
          <div className="stack" style={{ gap: 4 }}>
            <Link href={`/admin/entities/payment/${payment.id}`}>{shortId(payment.id)}</Link>
            <span className="muted">{payment.provider} · {shortId(payment.external_payment_id)}</span>
          </div>
        ),
        buyer: payment.buyer_email || '-',
        status: <DSBadge tone={payment.status === 'succeeded' ? 'success' : payment.status === 'failed' ? 'danger' : 'secondary'}>{payment.status}</DSBadge>,
        amount: money(payment.amount, payment.currency),
        order: (
          <div className="stack" style={{ gap: 4 }}>
            <Link href={`/admin/entities/order/${payment.order_id}`}>{shortId(payment.order_id)}</Link>
            <span className="muted">{statusLabel(payment.order_status)} · {statusLabel(payment.order_type)}</span>
          </div>
        ),
        entitlement: (
          <div className="stack" style={{ gap: 4 }}>
            <DSBadge tone={payment.entitlement_summary?.status === 'active' ? 'success' : 'secondary'}>
              {payment.entitlement_summary?.status || 'unknown'}
            </DSBadge>
            <span className="muted">
              {payment.entitlement_summary?.active || 0} active / {payment.entitlement_summary?.total || 0} total
            </span>
          </div>
        ),
        refunds: payment.refund_operations?.length || 0,
        updated: formatDate(payment.updated_at || payment.created_at),
      }))}
      getRowKey={(_, index) => payments[index]?.id || String(index)}
    />
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
    return <DSEmptyState title="Webhook events не найдены" description="Измени фильтры или обнови список." />;
  }

  return (
    <DSDataTable
      columns={[
        { key: 'webhook', label: 'Webhook' },
        { key: 'provider', label: 'Provider' },
        { key: 'event', label: 'Event' },
        { key: 'status', label: 'Status' },
        { key: 'payment', label: 'Payment' },
        { key: 'attempts', label: 'Attempts' },
        { key: 'received', label: 'Received' },
        { key: 'action', label: 'Action' },
      ]}
      rows={webhooks.map((webhook) => ({
        webhook: (
          <div className="stack" style={{ gap: 4 }}>
            <Link href={`/admin/entities/payment_webhook/${webhook.id}`}>{shortId(webhook.id)}</Link>
            <span className="muted">{shortId(webhook.external_event_id)}</span>
          </div>
        ),
        provider: webhook.provider,
        event: webhook.event_type,
        status: <DSBadge tone={webhook.status === 'failed' || webhook.status === 'rejected' ? 'danger' : 'secondary'}>{webhook.status}</DSBadge>,
        payment: webhook.payment_id ? <Link href={`/admin/entities/payment/${webhook.payment_id}`}>{shortId(webhook.payment_id)}</Link> : '-',
        attempts: webhook.attempts,
        received: formatDate(webhook.received_at || webhook.created_at),
        action: (
          <button
            type="button"
            className="button secondary sm"
            disabled={busyWebhookId === webhook.id}
            onClick={() => onReprocess(webhook)}
          >
            {busyWebhookId === webhook.id ? '...' : 'Reprocess'}
          </button>
        ),
      }))}
      getRowKey={(_, index) => webhooks[index]?.id || String(index)}
    />
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
      {loading ? <div className="card"><DSSkeleton lines={4} /></div> : null}

      <DSStatsGrid
        stats={[
          { label: 'Payments', value: state.payments.length, hint: `${paymentBuckets.succeeded || 0} succeeded`, tone: 'primary' },
          { label: 'Refund operations', value: refunds.length, hint: `${paymentBuckets.refunded || 0} refunded payments`, tone: refunds.length > 0 ? 'warning' : 'neutral' },
          {
            label: 'Webhook issues',
            value: (webhookBuckets.failed || 0) + (webhookBuckets.rejected || 0),
            hint: `${state.webhooks.length} loaded`,
            tone: (webhookBuckets.failed || 0) + (webhookBuckets.rejected || 0) > 0 ? 'danger' : 'success',
          },
          {
            label: 'Reconciliation',
            value: state.reconciliation?.status || '-',
            hint: `${state.reconciliation?.summary.total_issues || 0} issues`,
            tone: state.reconciliation?.status === 'ok' ? 'success' : 'warning',
          },
        ]}
      />

      <DSTransitionPanel active className="stack" style={{ gap: 24 }}>
      <DSSection
        title="Payment ledger"
        description="Payments, buyer, order and entitlement status."
        actions={
          <>
            <DSSelect
              label="Payment status"
              value={paymentFilters.status || ''}
              onChange={(event) => setPaymentFilters((prev) => ({ ...prev, status: event.target.value }))}
            >
              {PAYMENT_STATUSES.map((status) => (
                <option key={status || 'all'} value={status}>{status || 'all statuses'}</option>
              ))}
            </DSSelect>
            <DSTextField
              label="Provider"
              value={paymentFilters.provider || ''}
              onChange={(event) => setPaymentFilters((prev) => ({ ...prev, provider: event.target.value }))}
              placeholder="provider"
            />
            <DSTextField
              label="Buyer email"
              value={paymentFilters.buyer_email || ''}
              onChange={(event) => setPaymentFilters((prev) => ({ ...prev, buyer_email: event.target.value }))}
              placeholder="buyer email"
            />
            <button type="button" className="button secondary" onClick={() => void load()} disabled={loading}>
              {loading ? 'Loading...' : 'Refresh'}
            </button>
          </>
        }
      >
        <div className="card compact">
          <PaymentsTable payments={state.payments} />
        </div>
      </DSSection>

      <div className="grid-3">
        <DSSection title="Entitlement status" description="Payment-linked entitlement outcomes.">
          <div className="card compact stack" style={{ gap: 10 }}>
            {Object.entries(entitlementBuckets).map(([status, count]) => (
              <div className="list-item" key={status}>
                <DSStatusDot tone={status === 'active' ? 'success' : 'warning'} label={statusLabel(status)} />
                <strong>{count}</strong>
              </div>
            ))}
            {!Object.keys(entitlementBuckets).length ? <DSEmptyState title="Нет entitlement статусов" description="Статусы появятся после загрузки payments." /> : null}
          </div>
        </DSSection>
        <DSSection title="Payment statuses" description="Loaded payment status buckets.">
          <div className="card compact stack" style={{ gap: 10 }}>
            {Object.entries(paymentBuckets).map(([status, count]) => (
              <div className="list-item" key={status}>
                <DSStatusDot tone={status === 'succeeded' ? 'success' : status === 'failed' ? 'danger' : 'primary'} label={statusLabel(status)} />
                <strong>{count}</strong>
              </div>
            ))}
          </div>
        </DSSection>
        <DSSection title="Webhook statuses" description="Provider event intake buckets.">
          <div className="card compact stack" style={{ gap: 10 }}>
            {Object.entries(webhookBuckets).map(([status, count]) => (
              <div className="list-item" key={status}>
                <DSStatusDot tone={status === 'failed' || status === 'rejected' ? 'danger' : 'primary'} label={statusLabel(status)} />
                <strong>{count}</strong>
              </div>
            ))}
          </div>
        </DSSection>
      </div>

      <DSSection
        title="Provider event intake"
        description="Webhook events with reprocess action."
        actions={
          <>
            <DSSelect
              label="Webhook status"
              value={webhookFilters.status || ''}
              onChange={(event) => setWebhookFilters((prev) => ({ ...prev, status: event.target.value }))}
            >
              {WEBHOOK_STATUSES.map((status) => (
                <option key={status || 'all'} value={status}>{status || 'all statuses'}</option>
              ))}
            </DSSelect>
            <DSTextField
              label="Provider"
              value={webhookFilters.provider || ''}
              onChange={(event) => setWebhookFilters((prev) => ({ ...prev, provider: event.target.value }))}
              placeholder="provider"
            />
            <DSTextField
              label="Event type"
              value={webhookFilters.event_type || ''}
              onChange={(event) => setWebhookFilters((prev) => ({ ...prev, event_type: event.target.value }))}
              placeholder="event type"
            />
          </>
        }
      >
        <div className="card compact">
          <WebhooksTable webhooks={state.webhooks} onReprocess={reprocess} busyWebhookId={busyWebhookId} />
        </div>
      </DSSection>

      <DSSection title="Refund operations" description="Partial/full refund audit rows.">
        <div className="card compact">
        <RefundsTable refunds={refunds} />
        </div>
      </DSSection>

      <DSSection
        title="Provider payments, internal payments, entitlements"
        description={`Generated: ${formatDate(state.reconciliation?.generated_at)}`}
        actions={<DSBadge tone={(state.reconciliation?.summary.critical_count || 0) > 0 ? 'danger' : 'success'}>{state.reconciliation?.summary.critical_count || 0} critical</DSBadge>}
      >
        <div className="card compact">
          <IssueList issues={state.reconciliation?.issues || []} />
        </div>
      </DSSection>
      </DSTransitionPanel>
    </section>
  );
}
