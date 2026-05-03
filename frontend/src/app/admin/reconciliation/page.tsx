'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { adminReconciliationApi } from '@/modules/admin-reconciliation/api';
import type {
  AdminReconciliationReport,
  ReconciliationIssue,
  ReconciliationSection,
  ReconciliationSeverity,
  ReconciliationStatus,
  ReconciliationRepairAction,
  ReconciliationRepairResult,
} from '@/modules/admin-reconciliation/api';

type SectionIssue = ReconciliationIssue & { sectionKey: string };

const SECTION_ORDER = ['payments', 'orders', 'entitlements', 'payouts', 'webhooks', 'outbox'];
const SEVERITY_PRESETS = ['', 'critical', 'warning', 'info'];

function label(value: string) {
  return value.replaceAll('_', ' ');
}

function scalar(value: unknown, fallback = '—') {
  if (value === null || value === undefined || value === '') return fallback;
  if (typeof value === 'number') return value.toLocaleString('ru-RU');
  if (typeof value === 'boolean') return value ? 'yes' : 'no';
  if (Array.isArray(value)) return `${value.length} items`;
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

function formatDate(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('ru-RU');
}

function statusTitle(status: ReconciliationStatus) {
  if (status === 'ok') return 'OK';
  if (status === 'degraded') return 'Degraded';
  if (status === 'critical') return 'Critical';
  return status;
}

function statusDescription(status: ReconciliationStatus) {
  if (status === 'ok') return 'Деньги, доступы, webhooks и outbox согласованы.';
  if (status === 'degraded') return 'Есть предупреждения, нужна плановая проверка оператора.';
  if (status === 'critical') return 'Есть критичные расхождения между оплатами, доступами или выплатами.';
  return 'Статус получен от backend reconciliation service.';
}

function severityRank(severity: ReconciliationSeverity) {
  if (severity === 'critical') return 0;
  if (severity === 'warning') return 1;
  if (severity === 'info') return 2;
  return 3;
}

function Badge({ children }: { children: React.ReactNode }) {
  return <span className="badge secondary">{children}</span>;
}

function StatCard({ title, value, hint }: { title: string; value: React.ReactNode; hint?: string }) {
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

function MetricsPreview({ metrics }: { metrics?: Record<string, unknown> }) {
  const rows = Object.entries(metrics || {});
  if (!rows.length) return <p className="muted">Метрик нет.</p>;

  return (
    <div className="stack" style={{ gap: 10 }}>
      {rows.slice(0, 8).map(([key, value]) => (
        <div className="list-item" key={key}>
          <span className="muted">{label(key)}</span>
          <strong>{scalar(value)}</strong>
        </div>
      ))}
    </div>
  );
}

function SectionCard({ sectionKey, section }: { sectionKey: string; section?: ReconciliationSection }) {
  return (
    <div className="card">
      <div className="row" style={{ alignItems: 'flex-start', gap: 14 }}>
        <div className="stack" style={{ gap: 6 }}>
          <Badge>{label(sectionKey)}</Badge>
          <h2 className="title-md">{sectionKey}</h2>
          <p className="muted">{section?.checks?.length || 0} checks · {section?.issue_count || 0} issues</p>
        </div>
        <Badge>{section ? statusTitle(section.status) : 'missing'}</Badge>
      </div>
      <div style={{ marginTop: 16 }}>
        <MetricsPreview metrics={section?.metrics} />
      </div>
    </div>
  );
}


type RepairOption = {
  action: ReconciliationRepairAction;
  label: string;
  entity_type: string;
  entity_id: string;
  requiresForce?: boolean;
  reason: string;
};

function issueKey(issue: SectionIssue) {
  return `${issue.sectionKey}:${issue.code}:${issue.entity_type}:${issue.entity_id}`;
}

function recommendedRepairOptions(issue: SectionIssue): RepairOption[] {
  const options: RepairOption[] = [];
  const baseReason = `reconciliation:${issue.code}:${issue.sectionKey}`;

  if (issue.entity_type === 'outbox_message' || issue.code === 'outbox_delivery_problem') {
    options.push({
      action: 'retry_outbox',
      label: 'Retry outbox',
      entity_type: 'outbox_message',
      entity_id: issue.entity_id,
      reason: `${baseReason}:retry_outbox`,
    });
    options.push({
      action: 'mark_outbox_dead',
      label: 'Mark dead',
      entity_type: 'outbox_message',
      entity_id: issue.entity_id,
      reason: `${baseReason}:mark_outbox_dead`,
      requiresForce: true,
    });
  }

  if (issue.entity_type === 'payment_webhook' || issue.code === 'payment_webhook_problem') {
    options.push({
      action: 'reprocess_webhook',
      label: 'Reprocess webhook',
      entity_type: 'payment_webhook',
      entity_id: issue.entity_id,
      reason: `${baseReason}:reprocess_webhook`,
    });
  }

  if (issue.entity_type === 'order' && issue.code === 'completed_order_without_active_entitlement') {
    options.push({
      action: 'grant_order_access',
      label: 'Grant order access',
      entity_type: 'order',
      entity_id: issue.entity_id,
      reason: `${baseReason}:grant_order_access`,
    });
  }

  if (issue.entity_type === 'entitlement') {
    options.push({
      action: 'revoke_entitlement',
      label: 'Revoke entitlement',
      entity_type: 'entitlement',
      entity_id: issue.entity_id,
      reason: `${baseReason}:revoke_entitlement`,
      requiresForce: issue.severity === 'warning',
    });
  }

  if (issue.entity_type === 'payment' && issue.code === 'succeeded_payment_without_payout_accrual') {
    options.push({
      action: 'project_payout_accrual',
      label: 'Project payout accrual',
      entity_type: 'payment',
      entity_id: issue.entity_id,
      reason: `${baseReason}:project_payout_accrual`,
    });
  }

  if (issue.entity_type === 'payout_ledger' && issue.code === 'payout_accrual_for_non_success_payment') {
    options.push({
      action: 'reverse_payout_accrual',
      label: 'Reverse payout accrual',
      entity_type: 'payout_ledger',
      entity_id: issue.entity_id,
      reason: `${baseReason}:reverse_payout_accrual`,
      requiresForce: true,
    });
  }

  return options;
}

function RepairResultBlock({ result }: { result?: ReconciliationRepairResult | null }) {
  if (!result) return null;
  return (
    <div className="card success" style={{ marginTop: 14 }}>
      <div className="row" style={{ alignItems: 'flex-start', gap: 12 }}>
        <div className="stack" style={{ gap: 6 }}>
          <div className="inline" style={{ gap: 8, flexWrap: 'wrap' }}>
            <Badge>{result.status}</Badge>
            {result.audit?.event_type ? <Badge>{result.audit.event_type}</Badge> : null}
          </div>
          <strong>{result.message}</strong>
          <span className="muted">{result.action} · changed: {result.changed ? 'yes' : 'no'}</span>
        </div>
        <div className="inline" style={{ gap: 8, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
          {result.audit_event_href ? <Link href={result.audit_event_href} className="button secondary">Open audit event</Link> : null}
          {result.entity_href ? <Link href={result.entity_href} className="button ghost">Open target</Link> : null}
        </div>
      </div>
      <div className="grid-3" style={{ marginTop: 14 }}>
        <div className="list-item"><span className="muted">Audit event</span><strong>{result.audit_event_id || '—'}</strong></div>
        <div className="list-item"><span className="muted">Target</span><strong>{result.entity_type}:{result.entity_id}</strong></div>
        <div className="list-item"><span className="muted">Recorded</span><strong>{formatDate(result.audit?.created_at || null)}</strong></div>
      </div>
      <EvidenceBlock evidence={result.result} />
    </div>
  );
}

function LastRepairPanel({ result, onRefresh }: { result?: ReconciliationRepairResult | null; onRefresh: () => void }) {
  if (!result) return null;
  return (
    <div className="card success">
      <div className="row" style={{ alignItems: 'flex-start', gap: 12 }}>
        <div className="stack" style={{ gap: 8 }}>
          <div className="inline" style={{ gap: 8, flexWrap: 'wrap' }}>
            <Badge>last repair</Badge>
            <Badge>{result.status}</Badge>
            {result.changed ? <Badge>changed</Badge> : <Badge>no change</Badge>}
          </div>
          <h2 className="title-md">{result.message}</h2>
          <p className="muted">
            {result.action} · {result.entity_type}:{result.entity_id}
          </p>
        </div>
        <div className="inline" style={{ gap: 8, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
          {result.audit_event_href ? <Link href={result.audit_event_href} className="button secondary">Audit event</Link> : null}
          {result.entity_href ? <Link href={result.entity_href} className="button ghost">Target detail</Link> : null}
          <button className="button" type="button" onClick={onRefresh}>Refresh report</button>
        </div>
      </div>
    </div>
  );
}

function IssueRepairActions({ issue, onDone }: { issue: SectionIssue; onDone: (result: ReconciliationRepairResult) => void }) {
  const options = recommendedRepairOptions(issue);
  const [selectedAction, setSelectedAction] = useState(options[0]?.action || '');
  const selected = options.find((option) => option.action === selectedAction) || options[0];
  const [reason, setReason] = useState(selected?.reason || '');
  const [force, setForce] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<ReconciliationRepairResult | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const next = options.find((option) => option.action === selectedAction) || options[0];
    if (next && (!reason || reason.startsWith('reconciliation:'))) {
      setReason(next.reason);
    }
  }, [options, reason, selectedAction]);

  if (!options.length) {
    return (
      <div className="card" style={{ marginTop: 14 }}>
        <strong>Repair action</strong>
        <p className="muted" style={{ marginTop: 6 }}>
          Для этого типа расхождения пока нужен ручной разбор через detail page и audit trail.
        </p>
      </div>
    );
  }

  const submit = async () => {
    if (!selected) return;
    const normalizedReason = reason.trim();
    if (!normalizedReason) {
      setError('Reason обязателен для audited repair action.');
      return;
    }
    if (selected.requiresForce && !force) {
      setError('Для этого действия нужен force=true: это потенциально необратимая операция.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError('');
      setResult(null);
      const payload = await adminReconciliationApi.runRepair({
        action: selected.action,
        entity_type: selected.entity_type,
        entity_id: selected.entity_id,
        reason: normalizedReason,
        force,
      });
      setResult(payload);
      onDone(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Repair action failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="card" style={{ marginTop: 14 }}>
      <div className="row" style={{ alignItems: 'flex-start', gap: 12 }}>
        <div className="stack" style={{ gap: 6 }}>
          <strong>Audited repair</strong>
          <span className="muted">Действие запишется в audit log как admin.reconciliation.*</span>
        </div>
        <Badge>{selected?.entity_type || issue.entity_type}</Badge>
      </div>

      <div className="grid-4" style={{ marginTop: 14 }}>
        <label className="stack" style={{ gap: 6 }}>
          <span className="muted">Action</span>
          <select
            className="select"
            value={selectedAction}
            onChange={(event) => {
              const nextAction = event.target.value as ReconciliationRepairAction;
              const next = options.find((option) => option.action === nextAction);
              setSelectedAction(nextAction);
              setReason(next?.reason || '');
              setForce(false);
              setResult(null);
              setError('');
            }}
          >
            {options.map((option) => (
              <option key={`${option.action}-${option.entity_type}-${option.entity_id}`} value={option.action}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <div className="list-item"><span className="muted">Target type</span><strong>{selected?.entity_type || issue.entity_type}</strong></div>
        <div className="list-item"><span className="muted">Target id</span><strong>{selected?.entity_id || issue.entity_id}</strong></div>
        <label className="stack" style={{ gap: 6 }}>
          <span className="muted">Force</span>
          <span className="inline" style={{ gap: 8 }}>
            <input type="checkbox" checked={force} onChange={(event) => setForce(event.target.checked)} />
            <span className="muted">required for destructive/unsafe actions</span>
          </span>
        </label>
      </div>

      <label className="stack" style={{ gap: 6, marginTop: 14 }}>
        <span className="muted">Reason</span>
        <input
          className="input"
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          placeholder="Почему оператор запускает repair action"
        />
      </label>

      {error ? <div className="card error" style={{ marginTop: 14 }}>{error}</div> : null}
      <RepairResultBlock result={result} />

      <div className="inline" style={{ marginTop: 14 }}>
        <button className="button" type="button" disabled={isSubmitting} onClick={() => void submit()}>
          {isSubmitting ? 'Executing...' : 'Execute repair'}
        </button>
        <Link href="/admin/audit" className="button ghost">Audit feed</Link>
      </div>
    </div>
  );
}

function EvidenceBlock({ evidence }: { evidence?: Record<string, unknown> }) {
  const rows = Object.entries(evidence || {});
  if (!rows.length) return null;

  return (
    <details style={{ marginTop: 14 }}>
      <summary className="muted" style={{ cursor: 'pointer' }}>Evidence snapshot</summary>
      <div className="grid-2" style={{ marginTop: 12 }}>
        {rows.map(([key, value]) => (
          <div className="list-item" key={key}>
            <span className="muted">{label(key)}</span>
            <strong>{scalar(value)}</strong>
          </div>
        ))}
      </div>
    </details>
  );
}

function IssueCard({ issue, onRepairDone }: { issue: SectionIssue; onRepairDone: (result: ReconciliationRepairResult) => void }) {
  const entityHref = `/admin/entities/${issue.entity_type}/${issue.entity_id}`;
  const related = issue.related || [];

  return (
    <div className="card">
      <div className="row" style={{ alignItems: 'flex-start', gap: 16 }}>
        <div className="stack" style={{ gap: 8 }}>
          <div className="inline" style={{ gap: 8, flexWrap: 'wrap' }}>
            <Badge>{issue.severity}</Badge>
            <Badge>{label(issue.sectionKey)}</Badge>
            <Badge>{issue.code}</Badge>
          </div>
          <h2 className="title-md">{issue.message}</h2>
          <p className="muted">{issue.suggested_action}</p>
        </div>
        <Link href={entityHref} className="button secondary">Open entity</Link>
      </div>

      <div className="grid-3" style={{ marginTop: 16 }}>
        <div className="list-item"><span className="muted">Entity type</span><strong>{issue.entity_type}</strong></div>
        <div className="list-item"><span className="muted">Entity id</span><strong>{issue.entity_id}</strong></div>
        <div className="list-item"><span className="muted">Severity</span><strong>{issue.severity}</strong></div>
      </div>

      {related.length ? (
        <div className="stack" style={{ gap: 10, marginTop: 14 }}>
          <strong>Related entities</strong>
          <div className="inline" style={{ gap: 8, flexWrap: 'wrap' }}>
            {related.map((item) => (
              <Link
                href={item.href || `/admin/entities/${item.entity_type}/${item.entity_id}`}
                className="button ghost"
                key={`${item.entity_type}-${item.entity_id}`}
              >
                {item.label || item.entity_type}
              </Link>
            ))}
          </div>
        </div>
      ) : null}

      <EvidenceBlock evidence={issue.evidence} />
      <IssueRepairActions issue={issue} onDone={onRepairDone} />
    </div>
  );
}

export default function AdminReconciliationPage() {
  const { user } = useAuthSession();
  const isAdmin = user?.active_role === 'admin';
  const [report, setReport] = useState<AdminReconciliationReport | null>(null);
  const [limit, setLimit] = useState(100);
  const [sectionFilter, setSectionFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [msg, setMsg] = useState('');
  const [lastRepair, setLastRepair] = useState<ReconciliationRepairResult | null>(null);

  const load = useCallback(async () => {
    if (!isAdmin) return;
    try {
      setIsLoading(true);
      setMsg('');
      const payload = await adminReconciliationApi.getReport({ limit });
      setReport(payload);
    } catch (error) {
      setMsg(error instanceof Error ? error.message : 'Не удалось загрузить reconciliation report');
    } finally {
      setIsLoading(false);
    }
  }, [isAdmin, limit]);

  useEffect(() => {
    void load();
  }, [load]);

  const sections = useMemo(() => {
    const entries = Object.entries(report?.sections || {});
    return entries.sort(([left], [right]) => {
      const leftIndex = SECTION_ORDER.indexOf(left);
      const rightIndex = SECTION_ORDER.indexOf(right);
      return (leftIndex === -1 ? 999 : leftIndex) - (rightIndex === -1 ? 999 : rightIndex);
    });
  }, [report]);

  const issues = useMemo<SectionIssue[]>(() => {
    const rows: SectionIssue[] = [];
    for (const [sectionKey, section] of sections) {
      for (const issue of section?.issues || []) {
        rows.push({ ...issue, sectionKey });
      }
    }

    const normalizedQuery = query.trim().toLowerCase();
    return rows
      .filter((issue) => !sectionFilter || issue.sectionKey === sectionFilter)
      .filter((issue) => !severityFilter || issue.severity === severityFilter)
      .filter((issue) => {
        if (!normalizedQuery) return true;
        const haystack = `${issue.code} ${issue.entity_type} ${issue.entity_id} ${issue.message} ${issue.suggested_action}`.toLowerCase();
        return haystack.includes(normalizedQuery);
      })
      .sort((a, b) => severityRank(a.severity) - severityRank(b.severity));
  }, [query, sectionFilter, sections, severityFilter]);

  return (
    <ProtectedPage title="Admin reconciliation" description="Отчет по расхождениям между payment, order, entitlement, payout ledger, webhooks и outbox с audited repair actions.">
      {!isAdmin ? (
        <div className="card error">У текущей сессии нет admin-role.</div>
      ) : (
        <section className="stack" style={{ gap: 24 }}>
          <div className="row" style={{ alignItems: 'flex-start' }}>
            <div className="stack" style={{ gap: 10 }}>
              <span className="badge secondary">Money reconciliation</span>
              <h1>Admin reconciliation report</h1>
              <p className="lead">
                Проверка согласованности оплат, заказов, доступов, payout ledger, payment webhooks и outbox pipeline.
              </p>
            </div>
            <div className="inline" style={{ flexWrap: 'wrap', justifyContent: 'flex-end' }}>
              <Link href="/admin/operations" className="button secondary">Operations</Link>
              <Link href="/admin/audit" className="button ghost">Audit</Link>
              <button className="button" type="button" disabled={isLoading} onClick={() => void load()}>
                {isLoading ? 'Загрузка...' : 'Обновить'}
              </button>
            </div>
          </div>

          {msg ? <div className="card error">{msg}</div> : null}
          <LastRepairPanel result={lastRepair} onRefresh={() => void load()} />

          <div className={report?.status === 'critical' ? 'card error' : 'card'}>
            <div className="row" style={{ alignItems: 'center' }}>
              <div className="stack" style={{ gap: 8 }}>
                <div className="inline" style={{ gap: 8 }}>
                  <Badge>{report ? statusTitle(report.status) : 'loading'}</Badge>
                  <Badge>{report ? formatDate(report.generated_at) : '—'}</Badge>
                </div>
                <h2 className="title-md">{report ? statusDescription(report.status) : 'Загрузка reconciliation report...'}</h2>
              </div>
              <strong>{report?.summary.total_issues ?? 0} issues</strong>
            </div>
          </div>

          <div className="grid-4">
            <StatCard title="Total issues" value={report?.summary.total_issues ?? 0} />
            <StatCard title="Critical" value={report?.summary.critical_count ?? 0} hint="нужно исправить первым" />
            <StatCard title="Warnings" value={report?.summary.warning_count ?? 0} hint="операторская проверка" />
            <StatCard title="Sections" value={sections.length} hint="money/access/async checks" />
          </div>

          <div className="grid-3">
            {sections.map(([sectionKey, section]) => (
              <SectionCard key={sectionKey} sectionKey={sectionKey} section={section} />
            ))}
          </div>

          <div className="card">
            <div className="grid-4">
              <label className="stack" style={{ gap: 6 }}>
                <span className="muted">Section</span>
                <select className="select" value={sectionFilter} onChange={(event) => setSectionFilter(event.target.value)}>
                  <option value="">all sections</option>
                  {sections.map(([sectionKey]) => (
                    <option key={sectionKey} value={sectionKey}>{sectionKey}</option>
                  ))}
                </select>
              </label>
              <label className="stack" style={{ gap: 6 }}>
                <span className="muted">Severity</span>
                <select className="select" value={severityFilter} onChange={(event) => setSeverityFilter(event.target.value)}>
                  {SEVERITY_PRESETS.map((value) => (
                    <option key={value || 'all'} value={value}>{value || 'all severities'}</option>
                  ))}
                </select>
              </label>
              <label className="stack" style={{ gap: 6 }}>
                <span className="muted">Search</span>
                <input className="input" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="payment id / issue code / order" />
              </label>
              <label className="stack" style={{ gap: 6 }}>
                <span className="muted">Backend limit</span>
                <select className="select" value={limit} onChange={(event) => setLimit(Number(event.target.value))}>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                  <option value={250}>250</option>
                  <option value={500}>500</option>
                </select>
              </label>
            </div>
            <div className="inline" style={{ marginTop: 16 }}>
              <button className="button" type="button" disabled={isLoading} onClick={() => void load()}>Перезагрузить отчет</button>
              <button
                className="button ghost"
                type="button"
                disabled={isLoading}
                onClick={() => {
                  setSectionFilter('');
                  setSeverityFilter('');
                  setQuery('');
                  setLimit(100);
                }}
              >
                Сбросить фильтры
              </button>
            </div>
          </div>

          <div className="stack" style={{ gap: 16 }}>
            <div className="row">
              <h2 className="title-md">Issues</h2>
              <span className="muted">{issues.length} visible</span>
            </div>
            {isLoading ? <div className="card">Загрузка reconciliation report...</div> : null}
            {!isLoading && issues.length === 0 ? <div className="card">Расхождений по текущему фильтру нет.</div> : null}
            {issues.map((issue) => (
              <IssueCard
                key={issueKey(issue)}
                issue={issue}
                onRepairDone={(result) => {
                  setLastRepair(result);
                  void load();
                }}
              />
            ))}
          </div>
        </section>
      )}
    </ProtectedPage>
  );
}
