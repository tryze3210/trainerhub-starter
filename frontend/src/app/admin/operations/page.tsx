'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { isAdminUser } from '@/lib/authz';
import { adminEntityHref } from '@/modules/admin-entity-details/api';
import { adminOperationsApi } from '@/modules/admin-operations/api';
import type {
  JsonRecord,
  OperationsHubAction,
  OperationsHubPayload,
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
  if (typeof value === 'boolean') return value ? 'yes' : 'no';
  if (Array.isArray(value)) return `${value.length} items`;
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

function numberValue(value: unknown) {
  if (value === null || value === undefined || value === '') return 0;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function money(value: unknown, currency = 'RUB') {
  return `${scalar(value, '0.00')} ${currency}`;
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

function statusLabel(status?: OperationsStatus) {
  if (!status) return 'Missing';
  if (status === 'ok') return 'OK';
  if (status === 'degraded') return 'Degraded';
  if (status === 'critical') return 'Критично';
  if (status === 'missing') return 'Missing';
  if (status === 'unavailable') return 'Unavailable';
  return status;
}

function badgeClass(status?: string) {
  if (status === 'ok' || status === 'healthy' || status === 'improved') return 'badge success';
  if (status === 'critical' || status === 'failed' || status === 'worsened') return 'badge danger';
  if (status === 'degraded' || status === 'warning' || status === 'due') return 'badge warning';
  return 'badge secondary';
}

function actionResultSummary(value: unknown) {
  if (!value || typeof value !== 'object') return 'Операция выполнена';
  const result = value as JsonRecord;
  const importantKeys = ['status', 'processed', 'failed', 'claimed', 'requeued', 'matched', 'released_amount', 'id'];
  const parts = importantKeys
    .filter((key) => result[key] !== undefined && result[key] !== null)
    .map((key) => `${label(key)}: ${scalar(result[key])}`);
  return parts.length ? parts.join(' · ') : 'Операция выполнена';
}

function StatusBadge({ status }: { status?: OperationsStatus }) {
  return <span className={badgeClass(status)}>{statusLabel(status)}</span>;
}

function SeverityBadge({ severity }: { severity: string }) {
  return <span className={badgeClass(severity)}>{severity}</span>;
}

function StatCard({ title, value, hint, badge }: { title: string; value: ReactNode; hint?: string; badge?: ReactNode }) {
  return (
    <div className="card compact">
      <div className="row" style={{ alignItems: 'flex-start' }}>
        <div className="kpi">
          <small>{title}</small>
          <strong>{value}</strong>
          {hint ? <small>{hint}</small> : null}
        </div>
        {badge}
      </div>
    </div>
  );
}

function EmptyState({ children }: { children: ReactNode }) {
  return <div className="empty-state">{children}</div>;
}

function IssueList({ issues }: { issues?: OperationsIssue[] }) {
  if (!issues?.length) return <EmptyState>Активных проблем нет.</EmptyState>;
  return (
    <div className="stack">
      {issues.map((issue) => (
        <div className="row card compact shadow-none" key={`${issue.code}:${issue.severity}`}>
          <div>
            <strong>{label(issue.code)}</strong>
            <small>{issue.count !== undefined ? issue.count : issue.amount || '—'}</small>
          </div>
          <SeverityBadge severity={issue.severity} />
        </div>
      ))}
    </div>
  );
}

function KeyValueGrid({ data }: { data?: JsonRecord }) {
  const rows = Object.entries(data || {});
  if (!rows.length) return <EmptyState>Нет данных.</EmptyState>;
  return (
    <div className="grid-3">
      {rows.map(([key, value]) => (
        <div className="card compact shadow-none" key={key}>
          <small>{label(key)}</small>
          <strong>{scalar(value)}</strong>
        </div>
      ))}
    </div>
  );
}

function SectionCard({ title, description, section }: { title: string; description: string; section?: OperationsSection }) {
  return (
    <div className="card" id={title.toLowerCase().replaceAll(' ', '-')}>
      <div className="row" style={{ alignItems: 'flex-start' }}>
        <div>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>
        <StatusBadge status={section?.status || 'missing'} />
      </div>
      <div className="grid-2">
        <div>
          <h3>Проблемы</h3>
          <IssueList issues={section?.issues} />
        </div>
        <div>
          <h3>Количество</h3>
          <KeyValueGrid data={section?.counts} />
        </div>
      </div>
    </div>
  );
}

type OperationRunner = (title: string, action: () => Promise<unknown>) => void;

function OutboxTable({ rows, busy, onAction }: { rows?: OperationsRecentOutboxMessage[]; busy: boolean; onAction: OperationRunner }) {
  if (!rows?.length) return <EmptyState>Нет проблемных outbox-сообщений.</EmptyState>;
  return (
    <div className="card" id="outbox">
      <h2>Последние проблемы outbox</h2>
      <p>Повтор возвращает сообщение в обработку, а dead-letter исключает его из обработки.</p>
      <div className="stack">
        {rows.map((row) => (
          <div className="card compact shadow-none" key={row.id}>
            <div className="row">
              <div>
                <strong>{row.event_type || row.topic || 'event'}</strong>
                <small>
                  {row.status} · попытки: {row.attempts ?? 0} · {formatDate(row.updated_at)}
                </small>
                {row.last_error ? <small>{row.last_error}</small> : null}
                <small>
                  {row.aggregate_type}:{row.aggregate_id}
                </small>
              </div>
              <div className="inline">
                <Link className="btn secondary sm" href={adminEntityHref('outbox_message', row.id)}>
                  Открыть
                </Link>
                <button
                  className="btn sm"
                  disabled={busy}
                  onClick={() => onAction(`Retry outbox ${row.id}`, () => adminOperationsApi.retryOutboxMessage(row.id))}
                >
                  Повторить
                </button>
                <button
                  className="btn danger sm"
                  disabled={busy}
                  onClick={() => {
                    const reason = window.prompt('Причина перевода outbox message в dead-letter:', 'manual_ops_dead_letter');
                    if (!reason) return;
                    onAction(`Mark outbox ${row.id} dead`, () => adminOperationsApi.markOutboxDead(row.id, reason));
                  }}
                >
                  Dead-letter
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function WebhookTable({ rows }: { rows?: OperationsRecentWebhookEvent[] }) {
  if (!rows?.length) return <EmptyState>Нет проблемных событий вебхуков.</EmptyState>;
  return (
    <div className="card" id="webhooks">
      <h2>Последние проблемы вебхуков</h2>
      <div className="stack">
        {rows.map((row) => (
          <div className="card compact shadow-none" key={row.id}>
            <div className="row">
              <div>
                <strong>{row.event_type || 'webhook'}</strong>
                <small>
                  {row.provider || 'provider'} · {row.status || 'unknown'} · {formatDate(row.received_at)}
                </small>
                {row.error_message ? <small>{row.error_message}</small> : null}
              </div>
              <div className="inline">
                {row.payment_id ? (
                  <Link className="btn secondary sm" href={adminEntityHref('payment', row.payment_id)}>
                    Платеж
                  </Link>
                ) : null}
                <Link className="btn secondary sm" href={adminEntityHref('payment_webhook', row.id)}>
                  Открыть
                </Link>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function RiskPaymentsTable({ rows }: { rows?: OperationsRecentRiskPayment[] }) {
  if (!rows?.length) return <EmptyState>Нет платежей с возвратами, спорами или chargeback.</EmptyState>;
  return (
    <div className="card" id="payment-risk">
      <h2>Последние платежные риски</h2>
      <div className="stack">
        {rows.map((row) => (
          <div className="card compact shadow-none" key={row.id}>
            <div className="row">
              <div>
                <strong>{money(row.amount, row.currency || 'RUB')}</strong>
                <small>
                  {row.status} · {row.provider || 'provider'} · {formatDate(row.updated_at)}
                </small>
              </div>
              <div className="inline">
                {row.order_id ? (
                  <Link className="btn secondary sm" href={adminEntityHref('order', row.order_id)}>
                    Заказ
                  </Link>
                ) : null}
                <Link className="btn secondary sm" href={adminEntityHref('payment', row.id)}>
                  Открыть
                </Link>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function canReleaseRiskHold(row: OperationsRecentLedgerEntry) {
  return Boolean(row.source_id && row.entry_type === 'risk_hold' && row.source_type === 'payment_dispute_hold');
}

function RiskLedgerTable({ rows, busy, onAction }: { rows?: OperationsRecentLedgerEntry[]; busy: boolean; onAction: OperationRunner }) {
  if (!rows?.length) return <EmptyState>Нет риск- или reversal-записей реестра.</EmptyState>;
  return (
    <div className="card" id="payout-risk">
      <h2>Последние риски реестра выплат</h2>
      <div className="stack">
        {rows.map((row) => (
          <div className="card compact shadow-none" key={row.id}>
            <div className="row">
              <div>
                <strong>
                  {row.entry_type || 'entry'} · {money(row.amount, row.currency || 'RUB')}
                </strong>
                <small>
                  {row.direction || 'direction'} · {row.source_type || 'source'} · {formatDate(row.created_at)}
                </small>
                <small>
                  тренер {row.trainer_id || '—'} · источник {row.source_id || '—'}
                </small>
              </div>
              <div className="inline">
                <Link className="btn secondary sm" href={adminEntityHref('balance_entry', row.id)}>
                  Открыть
                </Link>
                {canReleaseRiskHold(row) ? (
                  <button
                    className="btn sm"
                    disabled={busy}
                    onClick={() => {
                      const reason = window.prompt('Причина ручного release risk hold:', 'manual_ops_release');
                      if (!reason || !row.source_id) return;
                      onAction(`Release risk hold ${row.source_id}`, () => adminOperationsApi.releaseRiskHold(String(row.source_id), reason));
                    }}
                  >
                    Снять холд
                  </button>
                ) : null}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ModerationCasesTable({ rows }: { rows?: OperationsRecentModerationCase[] }) {
  if (!rows?.length) return <EmptyState>Нет кейсов модерации платежных рисков.</EmptyState>;
  return (
    <div className="card" id="moderation-risk">
      <h2>Кейсы платежных рисков</h2>
      <div className="stack">
        {rows.map((row) => (
          <div className="card compact shadow-none" key={row.id}>
            <div className="row">
              <div>
                <strong>{row.title || 'Риск-кейс'}</strong>
                <small>
                  {row.status || 'статус'} · приоритет {row.priority ?? 0} · {formatDate(row.updated_at)}
                </small>
              </div>
              <div className="inline">
                {row.target_type && row.target_id ? (
                  <Link className="btn secondary sm" href={adminEntityHref(row.target_type, row.target_id)}>
                    Цель
                  </Link>
                ) : null}
                <Link className="btn secondary sm" href={adminEntityHref('moderation_case', row.id)}>
                  Открыть
                </Link>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function QuickActions({ actions, busy, onAction }: { actions?: OperationsHubAction[]; busy: boolean; onAction: OperationRunner }) {
  const supported = new Set(['capture_reconciliation_snapshot', 'evaluate_reconciliation_alerts', 'dispatch_outbox', 'requeue_stuck_outbox']);
  const visibleActions = (actions || []).filter((action) => supported.has(action.key));

  const run = (action: OperationsHubAction) => {
    if (action.key === 'capture_reconciliation_snapshot') {
      onAction(action.title, () => adminOperationsApi.captureReconciliationSnapshot());
    } else if (action.key === 'evaluate_reconciliation_alerts') {
      onAction(action.title, () => adminOperationsApi.evaluateReconciliationAlerts());
    } else if (action.key === 'dispatch_outbox') {
      onAction(action.title, () => adminOperationsApi.dispatchOutbox(100));
    } else if (action.key === 'requeue_stuck_outbox') {
      onAction(action.title, () => adminOperationsApi.requeueStuckOutbox({ older_than_minutes: 15, limit: 100 }));
    }
  };

  if (!visibleActions.length) return null;

  return (
    <div className="card">
      <h2>Быстрые действия</h2>
      <p>Безопасные действия оператора. Разрушающее исправление сверки остается в отдельном сценарии с токеном подтверждения.</p>
      <div className="grid-2">
        {visibleActions.map((action) => (
          <div className="card compact shadow-none" key={action.key}>
            <div className="row">
              <div>
                <strong>{action.title}</strong>
                <small>{action.description}</small>
                <small>
                  {action.method} · {action.api_href}
                </small>
              </div>
              <button className="btn sm" disabled={busy} onClick={() => run(action)}>
                Запустить
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ReconciliationPanel({ payload }: { payload: OperationsHubPayload | null }) {
  const reconciliation = payload?.sections.reconciliation;
  const metrics = reconciliation?.metrics as JsonRecord | undefined;
  const headline = (metrics?.headline || {}) as JsonRecord;
  const schedule = (reconciliation?.schedule || {}) as JsonRecord;
  const alerts = (reconciliation?.alerts || {}) as JsonRecord;
  const registry = reconciliation?.issue_registry;
  const issues = registry?.issues || [];

  return (
    <div className="card" id="reconciliation">
      <div className="row" style={{ alignItems: 'flex-start' }}>
        <div>
          <h2>Центр сверки</h2>
          <p>Снимок состояния, запланированный capture, алерты и нормализованный реестр проблем в одном блоке.</p>
        </div>
        <StatusBadge status={reconciliation?.status || 'missing'} />
      </div>

      <div className="grid-4">
        <StatCard title="Всего проблем" value={scalar(headline.current_total_issues ?? payload?.summary.reconciliation_total_issues)} hint="последний снимок" />
        <StatCard title="Критично" value={scalar(headline.current_critical_count ?? payload?.summary.reconciliation_critical_count)} hint="критичные проблемы" />
        <StatCard title="Можно исправить" value={scalar(payload?.summary.reconciliation_repairable_issues)} hint="реестр проблем" />
        <StatCard title="Алерты" value={scalar(payload?.summary.reconciliation_alert_count)} hint={alerts.has_alerts ? 'требует внимания' : 'активных алертов нет'} badge={<StatusBadge status={alerts.has_alerts ? 'critical' : 'ok'} />} />
      </div>

      <div className="grid-2" style={{ marginTop: 16 }}>
        <div className="card compact shadow-none">
          <h3>Запланированный снимок</h3>
          <KeyValueGrid
            data={{
              status: schedule.status,
              due: schedule.due,
              latest_generated_at: schedule.latest_generated_at,
              next_capture_due_at: schedule.next_capture_due_at,
            }}
          />
        </div>
        <div className="card compact shadow-none">
          <h3>Последнее направление</h3>
          <KeyValueGrid
            data={{
              latest_snapshot_id: payload?.summary.latest_reconciliation_snapshot_id,
              latest_status: payload?.summary.latest_reconciliation_status,
              direction: payload?.summary.latest_reconciliation_direction,
              source: headline.latest_source,
            }}
          />
        </div>
      </div>

      <div style={{ marginTop: 16 }}>
        <h3>Топ нормализованных проблем</h3>
        {!issues.length ? (
          <EmptyState>Нет нормализованных проблем сверки.</EmptyState>
        ) : (
          <div className="stack">
            {issues.slice(0, 10).map((issue) => {
              const id = String(issue.identity || `${issue.issue_code}:${issue.entity_type}:${issue.entity_id}`);
              return (
                <div className="card compact shadow-none" key={id}>
                  <div className="row">
                    <div>
                      <strong>{label(String(issue.issue_code || issue.code || 'issue'))}</strong>
                      <small>
                        {scalar(issue.entity_type)}:{scalar(issue.entity_id)} · {scalar(issue.section)}
                      </small>
                    </div>
                    <div className="inline">
                      <SeverityBadge severity={String(issue.severity || 'warning')} />
                      {issue.repairable ? <span className="badge success">можно исправить</span> : <span className="badge secondary">вручную</span>}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default function AdminОперацииPage() {
  const { user } = useAuthSession();
  const isAdmin = isAdminUser(user);
  const [hub, setHub] = useState<OperationsHubPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState('');
  const [msg, setMsg] = useState('');
  const [actionMsg, setActionMsg] = useState('');

  const load = useCallback(async () => {
    if (!isAdmin) return;
    try {
      setLoading(true);
      setMsg('');
      setHub(await adminOperationsApi.getHub({ snapshot_limit: 30, issue_limit: 20 }));
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить центр операций');
    } finally {
      setLoading(false);
    }
  }, [isAdmin]);

  const runAction: OperationRunner = useCallback(
    (title, action) => {
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
    },
    [load]
  );

  useEffect(() => {
    void load();
  }, [load]);

  const asyncInfra = hub?.sections.async_infra;
  const moneyRisk = hub?.sections.money_risk;
  const outbox = asyncInfra?.outbox;
  const webhooks = asyncInfra?.webhooks;
  const payments = moneyRisk?.payments;
  const payouts = moneyRisk?.payouts;
  const moderation = moneyRisk?.moderation;

  const topStats = useMemo(() => {
    const summary = hub?.summary || {};
    const outboxProblems =
      numberValue(outbox?.counts?.failed) + numberValue(outbox?.counts?.dead) + numberValue(outbox?.counts?.stuck_processing);
    const webhookProblems =
      numberValue(webhooks?.counts?.failed) + numberValue(webhooks?.counts?.rejected) + numberValue(webhooks?.counts?.stuck);
    const paymentRisk =
      numberValue(payments?.counts?.disputed) + numberValue(payments?.counts?.charged_back) + numberValue(payments?.counts?.refunded);
    return {
      operationsКритично: numberValue(summary.operations_critical_count),
      operationsПредупрежденияs: numberValue(summary.operations_warning_count),
      reconciliationПроблемы: numberValue(summary.reconciliation_total_issues),
      reconciliationКритично: numberValue(summary.reconciliation_critical_count),
      outboxProblems,
      webhookProblems,
      paymentRisk,
      lockedTotal: payouts?.amounts?.locked_total || '0.00',
    };
  }, [hub, outbox, payments, payouts, webhooks]);

  return (
    <ProtectedPage
      title="Операции администратора"
      description="Единый командный центр для async-инфраструктуры, платежных рисков, выплат, модерации и состояния сверки."
    >
      {!isAdmin ? (
        <div className="container page">
          <div className="card error">У текущей сессии нет роли администратора.</div>
        </div>
      ) : (
        <div className="container page stack">
          <div className="card hero">
            <div className="row" style={{ alignItems: 'flex-start' }}>
              <div>
                <span className="badge secondary">Операционный центр</span>
                <h1>Центр операций администратора</h1>
                <p>
                  Единая панель для outbox, вебхуков, платежных рисков, холдов выплат, модерации и состояния снимков сверки.
                </p>
                <small>Сформировано: {formatDate(hub?.generated_at)}</small>
              </div>
              <div className="inline">
                <StatusBadge status={hub?.status || 'missing'} />
                <button className="btn secondary" disabled={loading} onClick={() => void load()}>
                  {loading ? 'Загрузка...' : 'Обновить'}
                </button>
              </div>
            </div>

            <div className="grid-4" style={{ marginTop: 20 }}>
              <StatCard title="Критичные операции" value={topStats.operationsКритично} hint="операционная панель" badge={<StatusBadge status={topStats.operationsКритично ? 'critical' : 'ok'} />} />
              <StatCard title="Предупреждения операций" value={topStats.operationsПредупрежденияs} hint="предупреждения" />
              <StatCard title="Проблемы сверки" value={topStats.reconciliationПроблемы} hint={`${topStats.reconciliationКритично} критично`} badge={<StatusBadge status={topStats.reconciliationКритично ? 'critical' : 'ok'} />} />
              <StatCard title="Заблокированный риск выплат" value={money(topStats.lockedTotal)} hint="холды кошельков тренеров" />
            </div>

            <div className="grid-3" style={{ marginTop: 20 }}>
              <StatCard title="Проблемы outbox" value={topStats.outboxProblems} hint="ошибка / dead / зависло" />
              <StatCard title="Проблемы вебхуков" value={topStats.webhookProblems} hint="ошибка / отклонено / зависло" />
              <StatCard title="Платежные риски" value={topStats.paymentRisk} hint="споры / chargeback / возвраты" />
            </div>
          </div>

          {msg ? <div className="card error">{msg}</div> : null}
          {actionMsg ? <div className="card success">{actionMsg}</div> : null}

          <QuickActions actions={hub?.quick_actions} busy={Boolean(actionLoading)} onAction={runAction} />

          <div className="card">
            <h2>Навигация</h2>
            <div className="grid-3">
              {(hub?.navigation || []).map((item) => (
                <Link className="card compact shadow-none" href={item.href} key={item.key}>
                  <strong>{item.title}</strong>
                  <small>{item.description}</small>
                  {item.api_href ? <small>{item.api_href}</small> : null}
                </Link>
              ))}
            </div>
          </div>

          <ReconciliationPanel payload={hub} />

          <div className="grid-2">
            <SectionCard title="Outbox" description="Состояние отправки async-событий и зависшие/необрабатываемые сообщения." section={outbox} />
            <SectionCard title="Вебхуки" description="Прием вебхуков платежного провайдера и состояние обработки." section={webhooks} />
          </div>

          <OutboxTable rows={outbox?.recent_problem_messages} busy={Boolean(actionLoading)} onAction={runAction} />
          <WebhookTable rows={webhooks?.recent_problem_events} />

          <div className="grid-2">
            <SectionCard title="Платежи" description="Возвраты, споры, chargeback и риски неуспешных платежей." section={payments} />
            <SectionCard title="Выплаты" description="Холды кошельков тренеров, очередь выплат и состояние риск-реестра." section={payouts} />
          </div>

          <RiskPaymentsTable rows={payments?.recent_risk_payments} />
          <RiskLedgerTable rows={payouts?.recent_risk_ledger_entries} busy={Boolean(actionLoading)} onAction={runAction} />
          <ModerationCasesTable rows={moderation?.recent_payment_risk_cases} />
        </div>
      )}
    </ProtectedPage>
  );
}
