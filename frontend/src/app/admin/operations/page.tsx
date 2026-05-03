'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { adminOperationsApi } from '@/modules/admin-operations/api';
import { adminEntityHref } from '@/modules/admin-entity-details/api';
import type {
  AdminOperationsDashboard,
  OperationsBucket,
  OperationsIssue,
  OperationsRecentLedgerEntry,
  OperationsRecentModerationCase,
  OperationsRecentOutboxMessage,
  OperationsRecentRiskPayment,
  OperationsRecentWebhookEvent,
  OperationsSection,
  OperationsStatus,
} from '@/modules/admin-operations/api';

function scalar(value: unknown, fallback = '0') {
  if (value === null || value === undefined || value === '') return fallback;
  if (typeof value === 'number') return value.toLocaleString('ru-RU');
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

function numberValue(value: unknown) {
  if (value === null || value === undefined || value === '') return 0;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function money(value: unknown, currency = 'RUB') {
  const amount = scalar(value, '0.00');
  return `${amount} ${currency}`;
}

function formatDate(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('ru-RU');
}

function label(key: string) {
  return key.replaceAll('_', ' ');
}

function statusLabel(status: OperationsStatus) {
  if (status === 'ok') return 'OK';
  if (status === 'degraded') return 'Degraded';
  if (status === 'critical') return 'Critical';
  return status;
}

function statusDescription(status: OperationsStatus) {
  if (status === 'ok') return 'Система работает штатно';
  if (status === 'degraded') return 'Есть операционные предупреждения';
  if (status === 'critical') return 'Нужно вмешательство оператора';
  return 'Статус получен от backend';
}

function actionResultSummary(value: unknown) {
  if (!value || typeof value !== 'object') return 'Операция выполнена';
  const result = value as Record<string, unknown>;
  const importantKeys = ['status', 'processed', 'failed', 'claimed', 'requeued', 'matched', 'released_amount'];
  const parts = importantKeys
    .filter((key) => result[key] !== undefined && result[key] !== null)
    .map((key) => `${label(key)}: ${scalar(result[key])}`);
  return parts.length ? parts.join(' · ') : 'Операция выполнена';
}

function StatusBadge({ status }: { status: OperationsStatus }) {
  return <span className="badge secondary">{statusLabel(status)}</span>;
}

function SeverityBadge({ severity }: { severity: string }) {
  return <span className="badge secondary">{severity}</span>;
}

function StatCard({ label: title, value, hint }: { label: string; value: ReactNode; hint?: string }) {
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

function IssueList({ issues }: { issues?: OperationsIssue[] }) {
  if (!issues?.length) return <p className="muted">Активных проблем нет.</p>;

  return (
    <div className="stack" style={{ gap: 10 }}>
      {issues.map((issue) => (
        <div className="list-item" key={`${issue.code}-${issue.severity}`}>
          <span>
            <SeverityBadge severity={issue.severity} /> <span>{label(issue.code)}</span>
          </span>
          <strong>{issue.count !== undefined ? issue.count : issue.amount || '—'}</strong>
        </div>
      ))}
    </div>
  );
}

function KeyValueGrid({ data }: { data?: Record<string, string | number | null | undefined> }) {
  const rows = Object.entries(data || {});
  if (!rows.length) return <p className="muted">Нет данных.</p>;

  return (
    <div className="stack" style={{ gap: 10 }}>
      {rows.map(([key, value]) => (
        <div className="list-item" key={key}>
          <span className="muted">{label(key)}</span>
          <strong>{scalar(value)}</strong>
        </div>
      ))}
    </div>
  );
}

function BucketList({ rows }: { rows?: OperationsBucket[] }) {
  if (!rows?.length) return <p className="muted">Нет данных.</p>;

  return (
    <div className="stack" style={{ gap: 10 }}>
      {rows.map((row) => {
        const name = row.key || row.status || 'unknown';
        return (
          <div className="list-item" key={name}>
            <span className="muted">{label(name)}</span>
            <strong>{row.amount ? `${row.count} · ${row.amount}` : row.count}</strong>
          </div>
        );
      })}
    </div>
  );
}

function SectionCard({ title, description, section }: { title: string; description: string; section?: OperationsSection }) {
  return (
    <div className="card">
      <div className="inline" style={{ justifyContent: 'space-between', alignItems: 'flex-start', gap: 16 }}>
        <div>
          <h2 className="title-md">{title}</h2>
          <p className="muted" style={{ marginTop: 6 }}>{description}</p>
        </div>
        {section ? <StatusBadge status={section.status} /> : <span className="badge secondary">No data</span>}
      </div>

      <div className="stack" style={{ gap: 18, marginTop: 18 }}>
        <div>
          <h3 className="title-sm">Issues</h3>
          <div style={{ marginTop: 10 }}><IssueList issues={section?.issues} /></div>
        </div>

        <div>
          <h3 className="title-sm">Counts</h3>
          <div style={{ marginTop: 10 }}><KeyValueGrid data={section?.counts} /></div>
        </div>
      </div>
    </div>
  );
}

type OperationRunner = (label: string, action: () => Promise<unknown>) => void;

function OutboxTable({ rows, busy, onAction }: { rows?: OperationsRecentOutboxMessage[]; busy: boolean; onAction: OperationRunner }) {
  if (!rows?.length) return <div className="card"><p className="muted">Нет failed/dead outbox-сообщений.</p></div>;
  return (
    <div className="card">
      <div className="inline" style={{ justifyContent: 'space-between', alignItems: 'flex-start', gap: 16 }}>
        <div>
          <h2 className="title-md">Recent outbox problems</h2>
          <p className="muted" style={{ marginTop: 6 }}>Retry возвращает сообщение в обработку, Dead помечает его как необрабатываемое.</p>
        </div>
      </div>
      <div className="stack" style={{ gap: 10, marginTop: 16 }}>
        {rows.map((row) => (
          <div className="list-item" key={row.id}>
            <span>
              <strong>{row.event_type || row.topic || 'event'}</strong>
              <br />
              <span className="muted">{row.status} · attempts: {row.attempts ?? 0} · {formatDate(row.updated_at)}</span>
              {row.last_error ? <><br /><span className="muted">{row.last_error}</span></> : null}
              <br />
              <small className="muted">{row.aggregate_type}:{row.aggregate_id}</small>
            </span>
            <span className="inline" style={{ justifyContent: 'flex-end', gap: 8 }}>
              <Link href={adminEntityHref('outbox_message', row.id)} className="button ghost">Open</Link>
              <button
                className="button secondary"
                type="button"
                disabled={busy}
                onClick={() => onAction(`Retry outbox ${row.id}`, () => adminOperationsApi.retryOutboxMessage(row.id))}
              >
                Retry
              </button>
              <button
                className="button ghost"
                type="button"
                disabled={busy}
                onClick={() => {
                  const reason = window.prompt('Причина перевода outbox message в dead-letter:', 'manual_ops_dead_letter');
                  if (!reason) return;
                  onAction(`Mark outbox ${row.id} dead`, () => adminOperationsApi.markOutboxDead(row.id, reason));
                }}
              >
                Dead
              </button>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function WebhookTable({ rows }: { rows?: OperationsRecentWebhookEvent[] }) {
  if (!rows?.length) return <div className="card"><p className="muted">Нет проблемных webhook-событий.</p></div>;
  return (
    <div className="card">
      <h2 className="title-md">Recent webhook problems</h2>
      <div className="stack" style={{ gap: 10, marginTop: 16 }}>
        {rows.map((row) => (
          <div className="list-item" key={row.id}>
            <span>
              <strong>{row.event_type || 'webhook'}</strong>
              <br />
              <span className="muted">{row.provider || 'provider'} · {row.status || 'unknown'} · {formatDate(row.received_at)}</span>
              {row.error_message ? <><br /><span className="muted">{row.error_message}</span></> : null}
            </span>
            <span className="inline" style={{ justifyContent: 'flex-end', gap: 8 }}>
              {row.payment_id ? <Link href={adminEntityHref('payment', row.payment_id)} className="button ghost">Payment</Link> : null}
              <Link href={adminEntityHref('payment_webhook', row.id)} className="button secondary">Open</Link>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function RiskPaymentsTable({ rows }: { rows?: OperationsRecentRiskPayment[] }) {
  if (!rows?.length) return <div className="card"><p className="muted">Нет refund/dispute/chargeback платежей.</p></div>;
  return (
    <div className="card">
      <h2 className="title-md">Recent payment risk</h2>
      <div className="stack" style={{ gap: 10, marginTop: 16 }}>
        {rows.map((row) => (
          <div className="list-item" key={row.id}>
            <span>
              <strong>{money(row.amount, row.currency || 'RUB')}</strong>
              <br />
              <span className="muted">{row.status} · {row.provider || 'provider'} · {formatDate(row.updated_at)}</span>
            </span>
            <span className="inline" style={{ justifyContent: 'flex-end', gap: 8 }}>
              {row.order_id ? <Link href={adminEntityHref('order', row.order_id)} className="button ghost">Order</Link> : null}
              <Link href={adminEntityHref('payment', row.id)} className="button secondary">Open</Link>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function canReleaseRiskHold(row: OperationsRecentLedgerEntry) {
  return Boolean(
    row.source_id &&
      row.entry_type === 'risk_hold' &&
      row.source_type === 'payment_dispute_hold'
  );
}

function RiskLedgerTable({ rows, busy, onAction }: { rows?: OperationsRecentLedgerEntry[]; busy: boolean; onAction: OperationRunner }) {
  if (!rows?.length) return <div className="card"><p className="muted">Нет risk/reversal ledger-записей.</p></div>;
  return (
    <div className="card">
      <h2 className="title-md">Recent payout risk ledger</h2>
      <div className="stack" style={{ gap: 10, marginTop: 16 }}>
        {rows.map((row) => (
          <div className="list-item" key={row.id}>
            <span>
              <strong>{row.entry_type || 'entry'} · {money(row.amount, row.currency || 'RUB')}</strong>
              <br />
              <span className="muted">{row.direction || 'direction'} · {row.source_type || 'source'} · {formatDate(row.created_at)}</span>
              <br />
              <small className="muted">trainer {row.trainer_id || '—'} · source {row.source_id || '—'}</small>
            </span>
            <span className="inline" style={{ justifyContent: 'flex-end', gap: 8 }}>
              <Link href={adminEntityHref('payout_ledger', row.id)} className="button ghost">Open</Link>
              {canReleaseRiskHold(row) ? (
              <button
                className="button secondary"
                type="button"
                disabled={busy}
                onClick={() => {
                  const reason = window.prompt('Причина ручного release risk hold:', 'manual_ops_release');
                  if (!reason || !row.source_id) return;
                  onAction(`Release risk hold ${row.source_id}`, () => adminOperationsApi.releaseRiskHold(String(row.source_id), reason));
                }}
              >
                Release hold
              </button>
            ) : null}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ModerationCasesTable({ rows }: { rows?: OperationsRecentModerationCase[] }) {
  if (!rows?.length) return <div className="card"><p className="muted">Нет payment risk moderation cases.</p></div>;
  return (
    <div className="card">
      <h2 className="title-md">Payment risk cases</h2>
      <div className="stack" style={{ gap: 10, marginTop: 16 }}>
        {rows.map((row) => (
          <div className="list-item" key={row.id}>
            <span>
              <strong>{row.title || 'Risk case'}</strong>
              <br />
              <span className="muted">{row.status || 'status'} · priority {row.priority ?? 0} · {formatDate(row.updated_at)}</span>
            </span>
            <span className="inline" style={{ justifyContent: 'flex-end', gap: 8 }}>
              {row.target_type && row.target_id ? <Link href={adminEntityHref(row.target_type, row.target_id)} className="button ghost">Target</Link> : null}
              <Link href={adminEntityHref('moderation_case', row.id)} className="button secondary">Open</Link>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function AdminOperationsPage() {
  const { user } = useAuthSession();
  const isAdmin = user?.active_role === 'admin';
  const [dashboard, setDashboard] = useState<AdminOperationsDashboard | null>(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState('');
  const [msg, setMsg] = useState('');
  const [actionMsg, setActionMsg] = useState('');

  const load = useCallback(async () => {
    if (!isAdmin) return;
    try {
      setLoading(true);
      setMsg('');
      setDashboard(await adminOperationsApi.getDashboard());
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить operations dashboard');
    } finally {
      setLoading(false);
    }
  }, [isAdmin]);

  const runAction: OperationRunner = useCallback((title, action) => {
    void (async () => {
      try {
        setActionLoading(title);
        setActionMsg('');
        const result = await action();
        setActionMsg(`${title}: ${actionResultSummary(result)}`);
        await load();
      } catch (err) {
        setActionMsg(`${title}: ${err instanceof Error ? err.message : 'операция не выполнена'}`);
      } finally {
        setActionLoading('');
      }
    })();
  }, [load]);

  useEffect(() => {
    void load();
  }, [load]);

  const sections = dashboard?.sections || {};
  const outbox = sections.outbox;
  const webhooks = sections.webhooks;
  const payments = sections.payments;
  const payouts = sections.payouts;
  const moderation = sections.moderation;

  const topStats = useMemo(() => {
    const criticalCount = dashboard?.summary.critical_count || 0;
    const warningCount = dashboard?.summary.warning_count || 0;
    const outboxProblems = numberValue(outbox?.counts?.failed) + numberValue(outbox?.counts?.dead) + numberValue(outbox?.counts?.stuck_processing);
    const webhookProblems = numberValue(webhooks?.counts?.failed) + numberValue(webhooks?.counts?.rejected) + numberValue(webhooks?.counts?.stuck);
    const paymentRisk = numberValue(payments?.counts?.disputed) + numberValue(payments?.counts?.charged_back) + numberValue(payments?.counts?.refunded);
    const lockedTotal = payouts?.amounts?.locked_total || '0.00';
    return { criticalCount, warningCount, outboxProblems, webhookProblems, paymentRisk, lockedTotal };
  }, [dashboard, outbox, payments, payouts, webhooks]);

  return (
    <ProtectedPage title="Admin operations" description="Единая панель money risk, webhooks, outbox и payout holds.">
      {!isAdmin ? (
        <div className="card error">У текущей сессии нет admin-role.</div>
      ) : (
        <section className="stack" style={{ gap: 24 }}>
          <div className="card dark">
            <div className="stack" style={{ gap: 12 }}>
              <span className="badge secondary">Commerce operations</span>
              <h1 className="title-lg">Admin operations dashboard</h1>
              <p className="lead">
                Контроль проблемных денег и асинхронной инфраструктуры: payment webhooks, outbox, disputes, chargebacks, payout holds и payment-risk moderation.
              </p>
              <div className="inline" style={{ flexWrap: 'wrap' }}>
                <button className="button secondary" type="button" onClick={() => void load()} disabled={loading || Boolean(actionLoading)}>
                  {loading ? 'Refreshing...' : 'Refresh'}
                </button>
                <button
                  className="button secondary"
                  type="button"
                  disabled={Boolean(actionLoading)}
                  onClick={() => runAction('Dispatch outbox', () => adminOperationsApi.dispatchOutbox(100))}
                >
                  Dispatch outbox
                </button>
                <button
                  className="button secondary"
                  type="button"
                  disabled={Boolean(actionLoading)}
                  onClick={() => {
                    const minutes = window.prompt('Вернуть processing outbox старше N минут:', '15');
                    if (!minutes) return;
                    const parsed = Number(minutes);
                    runAction('Requeue stuck outbox', () => adminOperationsApi.requeueStuckOutbox({ older_than_minutes: Number.isFinite(parsed) ? parsed : 15, limit: 100 }));
                  }}
                >
                  Requeue stuck
                </button>
                <Link href="/admin/payouts" className="button ghost">Payout ops</Link>
                <Link href="/admin/moderation" className="button ghost">Moderation</Link>
                <Link href="/admin/analytics" className="button ghost">Analytics</Link>
                <Link href="/admin" className="button ghost">Back to cockpit</Link>
              </div>
            </div>
          </div>

          {msg ? <div className="card error">{msg}</div> : null}
          {actionMsg ? <div className="card">{actionLoading ? `${actionLoading}...` : actionMsg}</div> : null}
          {!dashboard && !msg ? <div className="card">Загрузка operations dashboard...</div> : null}

          {dashboard ? (
            <>
              <div className="grid-4">
                <StatCard label="Overall status" value={<StatusBadge status={dashboard.status} />} hint={statusDescription(dashboard.status)} />
                <StatCard label="Critical issues" value={topStats.criticalCount} />
                <StatCard label="Warnings" value={topStats.warningCount} />
                <StatCard label="Locked payout risk" value={money(topStats.lockedTotal)} />
              </div>

              <div className="grid-4">
                <StatCard label="Outbox problems" value={topStats.outboxProblems} hint="failed + dead + stuck" />
                <StatCard label="Webhook problems" value={topStats.webhookProblems} hint="failed + rejected + stuck" />
                <StatCard label="Payment risk events" value={topStats.paymentRisk} hint="disputed + chargeback + refunded" />
                <StatCard label="Generated at" value={formatDate(dashboard.generated_at)} />
              </div>

              <div className="grid-2">
                <SectionCard title="Outbox" description="Состояние event outbox и сообщений, требующих retry/dead-letter анализа." section={outbox} />
                <SectionCard title="Payment webhooks" description="Входящие webhook-и платежного провайдера, stuck/rejected/failed события." section={webhooks} />
                <SectionCard title="Payments risk" description="Refund, dispute, chargeback и неуспешные платежи." section={payments} />
                <SectionCard title="Payouts" description="Risk holds, locked balances, payout backlog и reversal ledger." section={payouts} />
              </div>

              <div className="grid-2">
                <div className="card">
                  <h2 className="title-md">Payment risk amounts</h2>
                  <div style={{ marginTop: 16 }}><KeyValueGrid data={payments?.risk_amounts} /></div>
                </div>
                <div className="card">
                  <h2 className="title-md">Payout amounts</h2>
                  <div style={{ marginTop: 16 }}><KeyValueGrid data={payouts?.amounts} /></div>
                </div>
              </div>

              <div className="grid-3">
                <div className="card">
                  <h2 className="title-md">Webhook statuses</h2>
                  <div style={{ marginTop: 16 }}><BucketList rows={webhooks?.by_status} /></div>
                </div>
                <div className="card">
                  <h2 className="title-md">Payout requests</h2>
                  <div style={{ marginTop: 16 }}><BucketList rows={payouts?.payout_request_by_status} /></div>
                </div>
                <div className="card">
                  <h2 className="title-md">Moderation risk</h2>
                  <div style={{ marginTop: 16 }}><BucketList rows={moderation?.case_by_status} /></div>
                </div>
              </div>

              <div className="grid-2">
                <OutboxTable rows={outbox?.recent_problem_messages} busy={Boolean(actionLoading)} onAction={runAction} />
                <WebhookTable rows={webhooks?.recent_problem_events} />
                <RiskPaymentsTable rows={payments?.recent_risk_payments} />
                <RiskLedgerTable rows={payouts?.recent_risk_ledger_entries} busy={Boolean(actionLoading)} onAction={runAction} />
              </div>

              <ModerationCasesTable rows={moderation?.recent_payment_risk_cases} />
            </>
          ) : null}
        </section>
      )}
    </ProtectedPage>
  );
}
