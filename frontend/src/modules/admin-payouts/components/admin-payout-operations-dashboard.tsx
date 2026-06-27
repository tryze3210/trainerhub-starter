'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { useAuthSession } from '@/components/auth-provider';
import { DSCard, DSSection, DSSkeleton, DSStatCard, DSStatusDot } from '@/design-system';
import {
  adminPayoutsApi,
  type AdminPayoutOverview,
  type AdminPayoutProjectionHealth,
  type AdminPayoutRequest,
  type AdminPayoutRiskHold,
  type AdminPayoutRiskHoldSummary,
  type PayoutAdminOpsFilters,
  type PayoutAdminOpsIntegritySnapshot,
  type PayoutAdminOpsRepairPreview,
  type PayoutAdminOpsReconciliationSnapshot,
  type PayoutAdminOpsRepairExecution,
  type PayoutRepairExecutionResult,
  type PayoutAdminOpsSummaryResponse,
  type PayoutReconciliationIssue,
  type PayoutReconciliationReport,
} from '@/modules/admin-payouts/api';
import { adminAuditApi, type AuditEvent } from '@/modules/admin-audit/api';

type DashboardState = {
  overview: AdminPayoutOverview | null;
  adminOps: PayoutAdminOpsSummaryResponse | null;
  adminOpsReconciliation: PayoutAdminOpsReconciliationSnapshot | null;
  payoutIntegrity: PayoutAdminOpsIntegritySnapshot | null;
  repairPreview: PayoutAdminOpsRepairPreview | null;
  lastRepairExecution: PayoutAdminOpsRepairExecution | null;
  payouts: AdminPayoutRequest[];
  reconciliation: PayoutReconciliationReport | null;
  riskSummary: AdminPayoutRiskHoldSummary | null;
  riskHolds: AdminPayoutRiskHold[];
  projection: AdminPayoutProjectionHealth | null;
  payoutExportAudits: AuditEvent[];
  repairAudits: AuditEvent[];
};

type PayoutAction = 'approve' | 'processing' | 'paid' | 'reject';

type BusyState = string | null;

const STATUS_OPTIONS = ['', 'pending', 'approved', 'processing', 'paid', 'rejected'];
const CURRENCY_OPTIONS = ['RUB', 'EUR', 'USD'];

const PAYOUT_EXPORT_AUDIT_FILTERS = {
  event_type: 'admin.payouts.admin_ops.csv_export',
  entity_type: 'payout_export',
  limit: 25,
};

const PAYOUT_REPAIR_AUDIT_FILTERS = {
  event_type: 'admin.payouts.repair_execution',
  entity_type: 'payout_repair_execution',
  limit: 25,
};

const PAYOUT_RECONCILIATION_EXPORT_AUDIT_FILTERS = {
  event_type: 'admin.payouts.reconciliation_report_export',
  entity_type: 'payout_reconciliation_export',
  limit: 25,
};

function money(value: string | number | null | undefined, currency = 'RUB') {
  const amount = Number(value ?? 0);
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
  }).format(Number.isFinite(amount) ? amount : 0);
}

function dateTime(value: string | null | undefined) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

function stringify(value: unknown) {
  if (value === null || value === undefined || value === '') return '—';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function auditBusinessContext(event: AuditEvent) {
  return asRecord(asRecord(event.context).context);
}

function auditContextValue(event: AuditEvent, key: string) {
  const root = asRecord(event.context);
  const nested = auditBusinessContext(event);
  return stringify(root[key] ?? nested[key]);
}

function mergeAuditEvents(...groups: AuditEvent[][]) {
  const byId = new Map<string, AuditEvent>();
  groups.flat().forEach((event) => byId.set(event.id, event));
  return Array.from(byId.values()).sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
}

function toneClass(status: string | undefined) {
  if (!status) return 'border-slate-200 bg-slate-50 text-slate-700';
  if (['paid', 'healthy', 'ok'].includes(status)) return 'border-emerald-200 bg-emerald-50 text-emerald-700';
  if (['rejected', 'failed', 'critical'].includes(status)) return 'border-rose-200 bg-rose-50 text-rose-700';
  if (['processing', 'approved', 'attention_required', 'degraded'].includes(status)) return 'border-amber-200 bg-amber-50 text-amber-700';
  return 'border-slate-200 bg-slate-50 text-slate-700';
}

function toneFromStatus(status: string | undefined): 'neutral' | 'primary' | 'success' | 'warning' | 'danger' {
  if (!status) return 'neutral';
  if (['paid', 'healthy', 'ok'].includes(status)) return 'success';
  if (['rejected', 'failed', 'critical'].includes(status)) return 'danger';
  if (['processing', 'approved', 'attention_required', 'degraded'].includes(status)) return 'warning';
  return 'neutral';
}

function MetricCard({ label, value, hint, status }: { label: string; value: string; hint?: string; status?: string }) {
  return <DSStatCard label={label} value={value} hint={hint} tone={toneFromStatus(status)} />;
}

function HealthIndicator({ label, status, detail }: { label: string; status: string; detail: string }) {
  return (
    <DSCard compact tone={toneFromStatus(status)}>
      <div className="row">
        <strong>{label}</strong>
        <DSStatusDot tone={toneFromStatus(status)} label={status} />
      </div>
      <p className="muted" style={{ marginTop: 8 }}>{detail}</p>
    </DSCard>
  );
}

function Section({ title, description, children }: { title: string; description?: string; children: ReactNode }) {
  return (
    <DSSection title={title} description={description}>
      <DSCard compact>{children}</DSCard>
    </DSSection>
  );
}

function actionAllowed(payout: AdminPayoutRequest, action: PayoutAction) {
  if (action === 'approve') return payout.status === 'pending' || payout.status === 'requested';
  if (action === 'processing') return payout.status === 'approved';
  if (action === 'paid') return payout.status === 'processing' || payout.status === 'approved';
  if (action === 'reject') return payout.status !== 'paid' && payout.status !== 'rejected';
  return false;
}

function actionLabel(action: PayoutAction) {
  if (action === 'approve') return 'Approve';
  if (action === 'processing') return 'Processing';
  if (action === 'paid') return 'Mark paid';
  return 'Reject';
}

function nextHint(payout: AdminPayoutRequest) {
  if (payout.status === 'pending' || payout.status === 'requested') return 'Следующий шаг: approve или reject.';
  if (payout.status === 'approved') return 'Следующий шаг: processing или mark-paid.';
  if (payout.status === 'processing') return 'Следующий шаг: mark-paid.';
  if (payout.status === 'paid') return 'Финальный статус: выплата закрыта.';
  if (payout.status === 'rejected') return payout.rejected_reason || 'Финальный статус: отклонена.';
  return 'Проверь статус вручную.';
}

function issuesFromSnapshot(snapshot: PayoutAdminOpsReconciliationSnapshot | null): PayoutReconciliationIssue[] {
  const payload = snapshot?.snapshot;
  if (!payload || typeof payload !== 'object' || !('issues' in payload) || !Array.isArray(payload.issues)) {
    return [];
  }
  return payload.issues as PayoutReconciliationIssue[];
}

function bucketCount(buckets: PayoutAdminOpsSummaryResponse['payout_buckets'] | undefined, status: string) {
  return buckets?.find((bucket) => bucket.status === status)?.count ?? 0;
}

export function AdminPayoutOperationsDashboard() {
  const { user } = useAuthSession();
  const isAdmin = user?.active_role === 'admin';

  const [state, setState] = useState<DashboardState>({
    overview: null,
    adminOps: null,
    adminOpsReconciliation: null,
    payoutIntegrity: null,
    repairPreview: null,
    lastRepairExecution: null,
    payouts: [],
    reconciliation: null,
    riskSummary: null,
    riskHolds: [],
    projection: null,
    payoutExportAudits: [],
    repairAudits: [],
  });
  const [statusFilter, setStatusFilter] = useState('');
  const [trainerFilter, setTrainerFilter] = useState('');
  const [currencyFilter, setCurrencyFilter] = useState('RUB');
  const [createdFrom, setCreatedFrom] = useState('');
  const [createdTo, setCreatedTo] = useState('');
  const [externalReference, setExternalReference] = useState('');
  const [rejectReason, setRejectReason] = useState('');
  const [releaseReason, setReleaseReason] = useState('manual_admin_release');
  const [repairBatchSize, setRepairBatchSize] = useState(25);
  const [selected, setSelected] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<BusyState>(null);
  const [message, setMessage] = useState('');

  const opsFilters = useMemo<PayoutAdminOpsFilters>(
    () => ({
      status: statusFilter || undefined,
      trainer_id: trainerFilter || undefined,
      currency: currencyFilter || undefined,
      created_from: createdFrom || undefined,
      created_to: createdTo || undefined,
      limit: 100,
    }),
    [createdFrom, createdTo, currencyFilter, statusFilter, trainerFilter]
  );

  const load = useCallback(async () => {
    if (!isAdmin) return;
    setLoading(true);
    setMessage('');
    try {
      const [
        overview,
        adminOps,
        payouts,
        reconciliation,
        adminOpsReconciliation,
        payoutIntegrity,
        repairPreview,
        riskSummary,
        riskHolds,
        projection,
        payoutExportAudits,
        reconciliationExportAudits,
        repairAudits,
      ] = await Promise.all([
        adminPayoutsApi.getOverview(),
        adminPayoutsApi.getAdminOpsSummary(opsFilters),
        adminPayoutsApi.listPayouts({ status: statusFilter || undefined, trainer_id: trainerFilter || undefined, limit: 100 }),
        adminPayoutsApi.getReconciliation(),
        adminPayoutsApi.getAdminOpsReconciliationSnapshot(opsFilters),
        adminPayoutsApi.getAdminOpsIntegritySnapshot(opsFilters),
        adminPayoutsApi.getAdminOpsRepairPreview({ ...opsFilters, batch_size: repairBatchSize }),
        adminPayoutsApi.getRiskHoldSummary(50),
        adminPayoutsApi.listRiskHolds({ trainer_id: trainerFilter || undefined, limit: 50 }),
        adminPayoutsApi.getProjectionHealth(),
        adminAuditApi.listEvents(PAYOUT_EXPORT_AUDIT_FILTERS),
        adminAuditApi.listEvents(PAYOUT_RECONCILIATION_EXPORT_AUDIT_FILTERS),
        adminAuditApi.listEvents(PAYOUT_REPAIR_AUDIT_FILTERS),
      ]);
      setState({
        overview,
        adminOps,
        payouts,
        reconciliation,
        adminOpsReconciliation,
        payoutIntegrity,
        repairPreview,
        lastRepairExecution: null,
        riskSummary,
        riskHolds,
        projection,
        payoutExportAudits: mergeAuditEvents(payoutExportAudits, reconciliationExportAudits),
        repairAudits,
      });
      setSelected((current) => current.filter((id) => payouts.some((payout) => payout.id === id)));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Не удалось загрузить admin payout operations');
    } finally {
      setLoading(false);
    }
  }, [isAdmin, opsFilters, repairBatchSize, statusFilter, trainerFilter]);

  useEffect(() => {
    void load();
  }, [load]);

  const stats = useMemo(() => {
    const buckets = new Map((state.overview?.statuses ?? []).map((bucket) => [bucket.status, bucket]));
    return {
      pending: buckets.get('pending')?.count ?? state.payouts.filter((payout) => payout.status === 'pending' || payout.status === 'requested').length,
      approved: buckets.get('approved')?.count ?? state.payouts.filter((payout) => payout.status === 'approved').length,
      processing: buckets.get('processing')?.count ?? state.payouts.filter((payout) => payout.status === 'processing').length,
      paid: buckets.get('paid')?.count ?? state.payouts.filter((payout) => payout.status === 'paid').length,
      rejected: buckets.get('rejected')?.count ?? state.payouts.filter((payout) => payout.status === 'rejected').length,
    };
  }, [state.overview?.statuses, state.payouts]);

  const adminOpsRecent = state.adminOps?.recent_payout_requests ?? state.adminOps?.recent_requests ?? [];
  const payoutBuckets = state.adminOps?.payout_buckets ?? state.adminOps?.status_buckets ?? [];
  const ledgerBuckets = state.adminOps?.ledger_buckets ?? [];
  const snapshotIssues = issuesFromSnapshot(state.adminOpsReconciliation);
  const integrityIssues = state.payoutIntegrity?.issues ?? [];
  const integrityIssueCodes = Object.entries(state.payoutIntegrity?.issue_codes ?? {}).sort((a, b) => b[1] - a[1]);
  const integritySeverities = Object.entries(state.payoutIntegrity?.issue_severities ?? {}).sort((a, b) => b[1] - a[1]);
  const repairPreviewActions = state.repairPreview?.actions ?? [];
  const repairActionCodes = Object.entries(state.repairPreview?.action_codes ?? {}).sort((a, b) => b[1] - a[1]);
  const totalPayouts = state.adminOps?.summary.total_payout_requests ?? state.payouts.length;
  const pendingPayouts = bucketCount(payoutBuckets, 'pending') + bucketCount(payoutBuckets, 'requested');
  const failedPayouts = bucketCount(payoutBuckets, 'failed') + bucketCount(payoutBuckets, 'rejected');
  const integrityIssueCount = state.payoutIntegrity?.summary?.issue_count ?? 0;
  const criticalIntegrityIssues = state.payoutIntegrity?.issue_severities?.critical ?? 0;
  const lastRepairRun = state.repairAudits[0] ?? null;
  const lastRepairContext = lastRepairRun ? auditBusinessContext(lastRepairRun) : {};
  const lastRepairSummary = lastRepairRun
    ? `fixed ${stringify(lastRepairContext.repaired_count)}, manual ${stringify(lastRepairContext.manual_review_count)}`
    : 'repair execution has not run yet';
  const payoutHealthStatus = failedPayouts > 0 ? 'critical' : pendingPayouts > 0 ? 'degraded' : 'healthy';
  const integrityHealthStatus = criticalIntegrityIssues > 0 ? 'critical' : integrityIssueCount > 0 ? 'degraded' : 'healthy';
  const repairHealthStatus = lastRepairRun ? 'healthy' : repairPreviewActions.length > 0 ? 'degraded' : 'healthy';
  const projectionHealthStatus = (state.projection?.failed_messages ?? 0) > 0 ? 'critical' : state.projection?.status || 'healthy';
  const riskHoldHealthStatus = (state.riskSummary?.shortfall_count ?? 0) > 0 ? 'critical' : (state.riskSummary?.active_hold_count ?? 0) > 0 ? 'degraded' : 'healthy';
  const healthIndicators = [
    {
      label: 'Payout queue',
      status: payoutHealthStatus,
      detail: `${pendingPayouts} pending, ${failedPayouts} failed/rejected`,
    },
    {
      label: 'Integrity',
      status: integrityHealthStatus,
      detail: `${integrityIssueCount} issues, ${criticalIntegrityIssues} critical`,
    },
    {
      label: 'Repair readiness',
      status: repairHealthStatus,
      detail: lastRepairRun ? `last run ${dateTime(lastRepairRun.created_at)} · ${lastRepairSummary}` : `${repairPreviewActions.length} preview actions`,
    },
    {
      label: 'Projection',
      status: projectionHealthStatus,
      detail: `${state.projection?.projected_messages ?? 0} projected, ${state.projection?.failed_messages ?? 0} failed`,
    },
    {
      label: 'Risk holds',
      status: riskHoldHealthStatus,
      detail: `${state.riskSummary?.active_hold_count ?? 0} active, ${state.riskSummary?.shortfall_count ?? 0} shortfalls`,
    },
  ];

  const repairIssueIds = (result: PayoutRepairExecutionResult) =>
    [result.payout_id ? `payout:${result.payout_id}` : '', result.wallet_id ? `wallet:${result.wallet_id}` : '', result.ledger_entry_id ? `ledger:${result.ledger_entry_id}` : '']
      .filter(Boolean)
      .join(' · ') || '—';

  const runAction = async (payout: AdminPayoutRequest, action: PayoutAction) => {
    if (action === 'reject' && !rejectReason.trim()) {
      setMessage('Reject reason обязателен для отклонения payout request.');
      return;
    }
    setBusy(`${action}:${payout.id}`);
    setMessage('');
    try {
      if (action === 'approve') await adminPayoutsApi.approve(payout.id, { external_reference: externalReference });
      if (action === 'processing') await adminPayoutsApi.markProcessing(payout.id, { external_reference: externalReference });
      if (action === 'paid') await adminPayoutsApi.markPaid(payout.id, { external_reference: externalReference });
      if (action === 'reject') await adminPayoutsApi.reject(payout.id, { reason: rejectReason.trim(), external_reference: externalReference });
      setMessage(`${actionLabel(action)} выполнен для payout ${payout.id}.`);
      await load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : `${actionLabel(action)} не выполнен`);
    } finally {
      setBusy(null);
    }
  };

  const runBulk = async (action: PayoutAction) => {
    if (!selected.length) {
      setMessage('Выбери хотя бы одну payout request.');
      return;
    }
    if (action === 'reject' && !rejectReason.trim()) {
      setMessage('Reject reason обязателен для bulk reject.');
      return;
    }
    setBusy(`bulk:${action}`);
    setMessage('');
    try {
      const result = await adminPayoutsApi.bulkTransition({
        payout_ids: selected,
        action,
        reason: action === 'reject' ? rejectReason.trim() : '',
        external_reference: externalReference,
      });
      const failed = result.results.filter((item) => !item.ok).length;
      setMessage(failed ? `Bulk ${action}: ${failed} ошибок из ${result.results.length}.` : `Bulk ${action}: выполнено ${result.results.length}.`);
      setSelected([]);
      await load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : `Bulk ${action} не выполнен`);
    } finally {
      setBusy(null);
    }
  };

  const runReconciliationRepair = async (dryRun: boolean) => {
    setBusy(dryRun ? 'reconciliation:dry-run' : 'reconciliation:apply');
    setMessage('');
    try {
      const result = await adminPayoutsApi.repairReconciliation(dryRun);
      setMessage(dryRun ? 'Payout reconciliation dry-run выполнен.' : `Payout reconciliation repair применён: ${stringify(result)}`);
      await load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Payout reconciliation repair не выполнен');
    } finally {
      setBusy(null);
    }
  };

  const runProjectOutbox = async () => {
    setBusy('projection:outbox');
    setMessage('');
    try {
      const result = await adminPayoutsApi.projectOutbox(100);
      setMessage(`Outbox projection запущен: ${stringify(result)}`);
      await load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Payout projection outbox не выполнен');
    } finally {
      setBusy(null);
    }
  };

  const executeRepair = async () => {
    setBusy('repair:execute');
    setMessage('');
    try {
      const result = await adminPayoutsApi.executeAdminOpsRepair({ ...opsFilters, batch_size: repairBatchSize });
      const [repairPreview, repairAudits, payoutIntegrity] = await Promise.all([
        adminPayoutsApi.getAdminOpsRepairPreview({ ...opsFilters, batch_size: repairBatchSize }),
        adminAuditApi.listEvents(PAYOUT_REPAIR_AUDIT_FILTERS),
        adminPayoutsApi.getAdminOpsIntegritySnapshot(opsFilters),
      ]);
      setState((current) => ({
        ...current,
        repairPreview,
        repairAudits,
        payoutIntegrity,
        lastRepairExecution: result,
      }));
      setMessage(`Repair execution: fixed ${result.summary?.repaired_count ?? 0}, manual review ${result.summary?.manual_review_count ?? 0}.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Payout repair execution не выполнен');
    } finally {
      setBusy(null);
    }
  };

  const releaseHold = async (hold: AdminPayoutRiskHold) => {
    if (!hold.payment_id) {
      setMessage('Risk hold не содержит payment_id.');
      return;
    }
    setBusy(`hold:${hold.id}`);
    setMessage('');
    try {
      await adminPayoutsApi.releaseRiskHold(hold.payment_id, releaseReason.trim() || 'manual_admin_release');
      setMessage(`Risk hold по payment ${hold.payment_id} отправлен на release.`);
      await load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Risk hold release не выполнен');
    } finally {
      setBusy(null);
    }
  };

  const runCsvExport = async (kind: 'requests' | 'ledger') => {
    setBusy(`csv:${kind}`);
    setMessage('');
    try {
      if (kind === 'requests') await adminPayoutsApi.exportAdminOpsRequestsCsv(opsFilters);
      if (kind === 'ledger') await adminPayoutsApi.exportAdminOpsLedgerCsv(opsFilters);
      const [payoutExportAudits, reconciliationExportAudits] = await Promise.all([
        adminAuditApi.listEvents(PAYOUT_EXPORT_AUDIT_FILTERS),
        adminAuditApi.listEvents(PAYOUT_RECONCILIATION_EXPORT_AUDIT_FILTERS),
      ]);
      setState((current) => ({ ...current, payoutExportAudits: mergeAuditEvents(payoutExportAudits, reconciliationExportAudits) }));
      setMessage(`CSV export ${kind} запущен и записан в audit trail.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : `CSV export ${kind} не выполнен`);
    } finally {
      setBusy(null);
    }
  };

  const runReconciliationExport = async (format: 'csv' | 'xlsx') => {
    setBusy(`reconciliation-export:${format}`);
    setMessage('');
    try {
      if (format === 'csv') await adminPayoutsApi.exportAdminOpsReconciliationReportCsv(opsFilters);
      if (format === 'xlsx') await adminPayoutsApi.exportAdminOpsReconciliationReportXlsx(opsFilters);
      const [payoutExportAudits, reconciliationExportAudits] = await Promise.all([
        adminAuditApi.listEvents(PAYOUT_EXPORT_AUDIT_FILTERS),
        adminAuditApi.listEvents(PAYOUT_RECONCILIATION_EXPORT_AUDIT_FILTERS),
      ]);
      setState((current) => ({ ...current, payoutExportAudits: mergeAuditEvents(payoutExportAudits, reconciliationExportAudits) }));
      setMessage(`Reconciliation report ${format.toUpperCase()} export запущен и записан в audit trail.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : `Reconciliation report ${format.toUpperCase()} export не выполнен`);
    } finally {
      setBusy(null);
    }
  };

  const runRepairAuditExport = async (format: 'csv' | 'xlsx') => {
    setBusy(`repair-audit-export:${format}`);
    setMessage('');
    try {
      if (format === 'csv') await adminPayoutsApi.exportAdminOpsRepairAuditCsv(opsFilters);
      if (format === 'xlsx') await adminPayoutsApi.exportAdminOpsRepairAuditXlsx(opsFilters);
      const repairAudits = await adminAuditApi.listEvents(PAYOUT_REPAIR_AUDIT_FILTERS);
      setState((current) => ({ ...current, repairAudits }));
      setMessage(`Repair audit ${format.toUpperCase()} export запущен.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : `Repair audit ${format.toUpperCase()} export не выполнен`);
    } finally {
      setBusy(null);
    }
  };

  const toggleSelected = (payoutId: string) => {
    setSelected((current) => (current.includes(payoutId) ? current.filter((value) => value !== payoutId) : [...current, payoutId]));
  };

  if (!isAdmin) {
    return <DSCard tone="warning">У текущей сессии нет admin-role.</DSCard>;
  }

  return (
    <div className="space-y-6">
      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-medium uppercase tracking-wide text-slate-500">Admin finance operations</p>
        <div className="mt-2 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-slate-950">Операции выплат</h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-600">
              Approve / processing / mark-paid / reject, payout ops summary, CSV exports, risk holds, projection и reconciliation snapshot.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50" href="/admin/operations">
              Operations hub
            </Link>
            <button className="rounded-xl bg-slate-950 px-4 py-2 text-sm font-medium text-white disabled:opacity-60" onClick={() => void load()} disabled={loading}>
              Обновить
            </button>
          </div>
        </div>
        {message ? <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-800">{message}</div> : null}
        {loading && state.payouts.length === 0 ? <div className="mt-4"><DSSkeleton lines={4} /></div> : null}
      </div>

      <Section title="Фильтры и meta" description="Эти фильтры применяются к payout queue, ops summary, reconciliation snapshot и CSV exports.">
        <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-7">
          <label className="text-sm font-medium text-slate-700">
            Статус
            <select className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              {STATUS_OPTIONS.map((status) => (
                <option key={status || 'all'} value={status}>
                  {status || 'Все'}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm font-medium text-slate-700">
            Currency
            <select className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2" value={currencyFilter} onChange={(event) => setCurrencyFilter(event.target.value)}>
              {CURRENCY_OPTIONS.map((currency) => (
                <option key={currency} value={currency}>
                  {currency}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm font-medium text-slate-700">
            Trainer id
            <input className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2" value={trainerFilter} onChange={(event) => setTrainerFilter(event.target.value)} placeholder="user_id или trainer profile id" />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Created from
            <input className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2" type="date" value={createdFrom} onChange={(event) => setCreatedFrom(event.target.value)} />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Created to
            <input className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2" type="date" value={createdTo} onChange={(event) => setCreatedTo(event.target.value)} />
          </label>
          <label className="text-sm font-medium text-slate-700">
            External reference
            <input className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2" value={externalReference} onChange={(event) => setExternalReference(event.target.value)} placeholder="bank-batch-042" />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Repair batch
            <input className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2" min={1} max={100} type="number" value={repairBatchSize} onChange={(event) => setRepairBatchSize(Math.max(1, Math.min(Number(event.target.value || 25), 100)))} />
          </label>
        </div>
      </Section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Total payout requests" value={String(state.adminOps?.summary.total_payout_requests ?? state.payouts.length)} hint="Под текущими фильтрами" />
        <MetricCard label="Active exposure" value={money(state.adminOps?.summary.active_payout_amount ?? state.overview?.ops.pending_exposure_amount, currencyFilter)} hint={`${state.adminOps?.summary.active_payout_count ?? state.overview?.ops.pending_exposure_count ?? 0} active requests`} status="approved" />
        <MetricCard label="Wallet available" value={money(state.adminOps?.wallet_totals?.available_amount ?? state.overview?.balances.available_amount, currencyFilter)} hint="Trainer wallet available" status="healthy" />
        <MetricCard label="Reconciliation" value={state.adminOpsReconciliation?.summary?.status ?? state.adminOps?.reconciliation?.status ?? state.reconciliation?.status ?? '—'} hint={`${state.adminOpsReconciliation?.summary?.issue_count ?? state.adminOps?.reconciliation?.issue_count ?? state.reconciliation?.issue_count ?? 0} issues`} status={state.adminOpsReconciliation?.summary?.status ?? state.reconciliation?.status} />
      </div>

      <Section title="Ops Dashboard" description="Production-readiness view for payout operations health.">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <MetricCard label="Total payouts" value={String(totalPayouts)} hint="All payout requests under filters" />
          <MetricCard label="Pending payouts" value={String(pendingPayouts)} hint="requested + pending" status={pendingPayouts ? 'degraded' : 'healthy'} />
          <MetricCard label="Failed payouts" value={String(failedPayouts)} hint="failed + rejected" status={failedPayouts ? 'critical' : 'healthy'} />
          <MetricCard label="Integrity issues" value={String(integrityIssueCount)} hint={`${criticalIntegrityIssues} critical`} status={integrityHealthStatus} />
          <MetricCard label="Last repair run" value={lastRepairRun ? dateTime(lastRepairRun.created_at) : '—'} hint={lastRepairSummary} status={repairHealthStatus} />
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          {healthIndicators.map((item) => (
            <HealthIndicator detail={item.detail} key={item.label} label={item.label} status={item.status} />
          ))}
        </div>
      </Section>

      <Section title="Payout admin-ops summary" description="Read-only финансовая сводка из /payouts/admin-ops/summary/.">
        <div className="grid gap-4 xl:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 p-4">
            <h3 className="font-semibold text-slate-900">Wallet totals</h3>
            <dl className="mt-3 space-y-2 text-sm">
              <div className="flex justify-between gap-3"><dt className="text-slate-500">Available</dt><dd>{money(state.adminOps?.wallet_totals?.available_amount, currencyFilter)}</dd></div>
              <div className="flex justify-between gap-3"><dt className="text-slate-500">Pending</dt><dd>{money(state.adminOps?.wallet_totals?.pending_amount, currencyFilter)}</dd></div>
              <div className="flex justify-between gap-3"><dt className="text-slate-500">Locked/reserved</dt><dd>{money(state.adminOps?.wallet_totals?.locked_amount ?? state.adminOps?.wallet_totals?.reserved_amount, currencyFilter)}</dd></div>
              <div className="flex justify-between gap-3"><dt className="text-slate-500">Trainers</dt><dd>{state.adminOps?.wallet_totals?.trainers_count ?? '—'}</dd></div>
            </dl>
          </div>
          <div className="rounded-2xl border border-slate-200 p-4">
            <h3 className="font-semibold text-slate-900">Status buckets</h3>
            <div className="mt-3 space-y-2 text-sm">
              {payoutBuckets.slice(0, 6).map((bucket, index) => (
                <div className="flex items-center justify-between gap-3" key={`${bucket.status || 'bucket'}:${index}`}>
                  <span className={`rounded-full border px-2 py-1 text-xs ${toneClass(bucket.status)}`}>{bucket.status || 'unknown'}</span>
                  <span>{bucket.count} · {money(bucket.amount, bucket.currency || currencyFilter)}</span>
                </div>
              ))}
              {!payoutBuckets.length ? <p className="text-slate-500">Buckets отсутствуют.</p> : null}
            </div>
          </div>
          <div className="rounded-2xl border border-slate-200 p-4">
            <h3 className="font-semibold text-slate-900">Ledger buckets</h3>
            <div className="mt-3 space-y-2 text-sm">
              {ledgerBuckets.slice(0, 6).map((bucket, index) => (
                <div className="flex items-center justify-between gap-3" key={`${bucket.entry_type || 'ledger'}:${bucket.direction || 'direction'}:${index}`}>
                  <span className="text-slate-600">{bucket.entry_type || 'unknown'} {bucket.direction ? `· ${bucket.direction}` : ''}</span>
                  <span>{bucket.count} · {money(bucket.amount, bucket.currency || currencyFilter)}</span>
                </div>
              ))}
              {!ledgerBuckets.length ? <p className="text-slate-500">Ledger buckets отсутствуют.</p> : null}
            </div>
          </div>
        </div>
      </Section>

      <Section title="Exports" description="Выгрузки используют текущие фильтры и audit-логируются backend-слоем.">
        <div className="flex flex-wrap gap-3">
          <button className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-60" onClick={() => void runCsvExport('requests')} disabled={!!busy}>
            Export payout requests CSV
          </button>
          <button className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-60" onClick={() => void runCsvExport('ledger')} disabled={!!busy}>
            Export payout ledger CSV
          </button>
          <button className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-60" onClick={() => void runReconciliationExport('csv')} disabled={!!busy}>
            Export reconciliation CSV
          </button>
          <button className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-60" onClick={() => void runReconciliationExport('xlsx')} disabled={!!busy}>
            Export reconciliation XLSX
          </button>
        </div>
      </Section>

      <Section title="Recent payout exports" description="Последние audit events по payout exports. Используется общий admin audit trail, поэтому видны actor, фильтры и размер выгрузки.">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-3 py-2">Created</th>
                <th className="px-3 py-2">Actor</th>
                <th className="px-3 py-2">Export</th>
                <th className="px-3 py-2">Rows</th>
                <th className="px-3 py-2">Details</th>
                <th className="px-3 py-2">Filters</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {state.payoutExportAudits.slice(0, 8).map((event) => (
                <tr key={event.id}>
                  <td className="px-3 py-2 whitespace-nowrap">{dateTime(event.created_at)}</td>
                  <td className="px-3 py-2">{event.actor_email || event.actor || '—'}</td>
                  <td className="px-3 py-2">
                    <div className="font-medium text-slate-900">{event.entity_id || auditContextValue(event, 'export_type')}</div>
                    <div className="text-xs text-slate-500">{event.event_type}</div>
                  </td>
                  <td className="px-3 py-2">
                    {auditContextValue(event, 'exported_rows')} / {auditContextValue(event, 'total_rows')}
                  </td>
                  <td className="px-3 py-2">{auditContextValue(event, 'truncated') !== '—' ? auditContextValue(event, 'truncated') : auditContextValue(event, 'section_counts')}</td>
                  <td className="px-3 py-2 max-w-md truncate" title={auditContextValue(event, 'filters')}>
                    {auditContextValue(event, 'filters')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!state.payoutExportAudits.length ? <p className="p-4 text-sm text-slate-500">Payout export audit events пока отсутствуют.</p> : null}
        </div>
      </Section>

      <Section title="Ops controls" description="Все действия идут через backend state-machine и пишут audit events.">
        <div className="flex flex-wrap gap-2">
          <button className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-60" onClick={() => void runProjectOutbox()} disabled={!!busy}>Project outbox</button>
          <button className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-60" onClick={() => void runReconciliationRepair(true)} disabled={!!busy}>Dry-run repair</button>
          <button className="rounded-xl border border-amber-300 bg-amber-50 px-4 py-2 text-sm font-medium text-amber-900 hover:bg-amber-100 disabled:opacity-60" onClick={() => void runReconciliationRepair(false)} disabled={!!busy}>Apply repair</button>
          <button className="rounded-xl border border-emerald-300 bg-emerald-50 px-4 py-2 text-sm font-medium text-emerald-900 hover:bg-emerald-100 disabled:opacity-60" onClick={() => void executeRepair()} disabled={!!busy || !repairPreviewActions.length}>
            Execute payout repair
          </button>
        </div>
        <p className="mt-3 text-sm text-slate-600">
          {state.projection?.status || 'projection —'} · {state.projection?.consumer || 'payout projection'} · projected: {state.projection?.projected_messages ?? 0}, failed: {state.projection?.failed_messages ?? 0}
        </p>
      </Section>

      <Section title="Bulk actions" description="Bulk reject требует reason. External reference попадёт в transition payload.">
        <div className="grid gap-3 md:grid-cols-[1fr_2fr]">
          <label className="text-sm font-medium text-slate-700">
            Reject reason
            <input className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2" value={rejectReason} onChange={(event) => setRejectReason(event.target.value)} placeholder="Неверные реквизиты" />
          </label>
          <div className="flex flex-wrap items-end gap-2">
            <span className="w-full text-sm text-slate-600">Выбрано payout requests: {selected.length}</span>
            <button className="rounded-xl border px-3 py-2 text-sm disabled:opacity-60" onClick={() => void runBulk('approve')} disabled={!selected.length || !!busy}>Approve selected</button>
            <button className="rounded-xl border px-3 py-2 text-sm disabled:opacity-60" onClick={() => void runBulk('processing')} disabled={!selected.length || !!busy}>Processing selected</button>
            <button className="rounded-xl border px-3 py-2 text-sm disabled:opacity-60" onClick={() => void runBulk('paid')} disabled={!selected.length || !!busy}>Paid selected</button>
            <button className="rounded-xl border px-3 py-2 text-sm disabled:opacity-60" onClick={() => void runBulk('reject')} disabled={!selected.length || !!busy}>Reject selected</button>
          </div>
        </div>
      </Section>

      <Section title="Payout queue" description="Текущая очередь выплат и state-machine actions.">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-3 py-2">Select</th>
                <th className="px-3 py-2">Created</th>
                <th className="px-3 py-2">Trainer</th>
                <th className="px-3 py-2">Amount</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Destination</th>
                <th className="px-3 py-2">Next</th>
                <th className="px-3 py-2">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {state.payouts.map((payout) => (
                <tr key={payout.id}>
                  <td className="px-3 py-2"><input checked={selected.includes(payout.id)} onChange={() => toggleSelected(payout.id)} type="checkbox" /></td>
                  <td className="px-3 py-2">{dateTime(payout.requested_at || payout.created_at)}</td>
                  <td className="px-3 py-2">{payout.trainer_id || '—'}</td>
                  <td className="px-3 py-2">{money(payout.amount, payout.currency)}</td>
                  <td className="px-3 py-2"><span className={`rounded-full border px-2 py-1 text-xs ${toneClass(payout.status)}`}>{payout.status}</span></td>
                  <td className="px-3 py-2">{payout.destination_masked || '—'}</td>
                  <td className="px-3 py-2 text-slate-600">{nextHint(payout)}</td>
                  <td className="px-3 py-2">
                    <div className="flex flex-wrap gap-1">
                      {(['approve', 'processing', 'paid', 'reject'] as PayoutAction[]).map((action) => (
                        <button className="rounded-lg border px-2 py-1 text-xs disabled:opacity-40" disabled={!actionAllowed(payout, action) || busy === `${action}:${payout.id}`} key={action} onClick={() => void runAction(payout, action)}>
                          {actionLabel(action)}
                        </button>
                      ))}
                      <Link className="rounded-lg border px-2 py-1 text-xs" href={`/admin/payouts/${payout.id}`}>Detail</Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!state.payouts.length ? <p className="p-4 text-sm text-slate-500">Нет payout requests под выбранный фильтр.</p> : null}
        </div>
      </Section>

      <Section title="Recent admin-ops payout requests" description="Последние заявки из /payouts/admin-ops/summary/.">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {adminOpsRecent.slice(0, 6).map((payout) => (
            <div className="rounded-2xl border border-slate-200 p-4" key={`ops:${payout.id}`}>
              <div className="flex items-center justify-between gap-3">
                <span className={`rounded-full border px-2 py-1 text-xs ${toneClass(payout.status)}`}>{payout.status}</span>
                <span className="font-semibold">{money(payout.amount, payout.currency)}</span>
              </div>
              <p className="mt-2 text-xs text-slate-500">{payout.id}</p>
              <p className="mt-1 text-sm text-slate-600">trainer: {payout.trainer_id || '—'} · {dateTime(payout.created_at || payout.requested_at)}</p>
            </div>
          ))}
          {!adminOpsRecent.length ? <p className="text-sm text-slate-500">Admin-ops summary не вернул recent requests.</p> : null}
        </div>
      </Section>

      <Section title="Risk holds" description={`Active amount: ${money(state.riskSummary?.active_hold_amount, currencyFilter)} · active count: ${state.riskSummary?.active_hold_count ?? 0}`}>
        <label className="mb-3 block text-sm font-medium text-slate-700">
          Release reason
          <input className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 md:w-96" value={releaseReason} onChange={(event) => setReleaseReason(event.target.value)} />
        </label>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {state.riskHolds.slice(0, 8).map((hold) => (
            <div className="rounded-2xl border border-slate-200 p-4" key={hold.id}>
              <div className="flex items-center justify-between gap-2">
                <span className={`rounded-full border px-2 py-1 text-xs ${toneClass(hold.status)}`}>{hold.status}</span>
                <span className="font-semibold">{money(hold.active_amount ?? hold.amount, hold.currency)}</span>
              </div>
              <p className="mt-2 text-xs text-slate-500">payment: {hold.payment_id || '—'}</p>
              <p className="mt-1 text-xs text-slate-500">trainer: {hold.trainer_id || '—'}</p>
              <button className="mt-3 rounded-xl border border-slate-200 px-3 py-2 text-sm disabled:opacity-50" onClick={() => void releaseHold(hold)} disabled={!hold.payment_id || busy === `hold:${hold.id}`}>
                Release
              </button>
            </div>
          ))}
          {!state.riskHolds.length ? <p className="text-sm text-slate-500">Active risk holds не найдены.</p> : null}
        </div>
      </Section>

      <Section title="Integrity Issues" description="Read-only диагностика payout requests, wallets и ledger без repair actions.">
        <div className="mb-4 grid gap-4 md:grid-cols-4">
          <MetricCard label="Integrity status" value={state.payoutIntegrity?.summary?.status || '—'} hint={`${state.payoutIntegrity?.summary?.issue_count ?? 0} issues`} status={state.payoutIntegrity?.summary?.status} />
          <MetricCard label="Wallets scanned" value={String(state.payoutIntegrity?.summary?.wallet_count ?? 0)} hint="TrainerWallet rows" />
          <MetricCard label="Payouts scanned" value={String(state.payoutIntegrity?.summary?.payouts_scanned ?? 0)} hint="Filtered PayoutRequest rows" />
          <MetricCard label="Ledger scanned" value={String(state.payoutIntegrity?.summary?.ledger_entries_scanned ?? 0)} hint="Filtered BalanceEntry rows" />
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 p-4">
            <h3 className="font-medium text-slate-900">Issue severities</h3>
            <div className="mt-3 flex flex-wrap gap-2">
              {integritySeverities.map(([severity, count]) => (
                <span className={`rounded-full border px-3 py-1 text-xs ${toneClass(severity)}`} key={severity}>{severity}: {count}</span>
              ))}
              {!integritySeverities.length ? <span className="text-sm text-slate-500">Severity buckets отсутствуют.</span> : null}
            </div>
          </div>
          <div className="rounded-2xl border border-slate-200 p-4">
            <h3 className="font-medium text-slate-900">Issue codes</h3>
            <div className="mt-3 grid gap-2 text-sm text-slate-700">
              {integrityIssueCodes.slice(0, 8).map(([code, count]) => (
                <div className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2" key={code}>
                  <span className="font-mono text-xs">{code}</span>
                  <span className="font-semibold">{count}</span>
                </div>
              ))}
              {!integrityIssueCodes.length ? <span className="text-sm text-slate-500">Issue codes отсутствуют.</span> : null}
            </div>
          </div>
        </div>

        <div className="mt-4 overflow-x-auto rounded-2xl border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-3 py-2">Severity</th>
                <th className="px-3 py-2">Code</th>
                <th className="px-3 py-2">Entity</th>
                <th className="px-3 py-2">Amount</th>
                <th className="px-3 py-2">Message</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {integrityIssues.slice(0, 12).map((issue, index) => (
                <tr key={`${issue.code}:${issue.payout_id || issue.wallet_id || issue.ledger_entry_id || index}`}>
                  <td className="px-3 py-2"><span className={`rounded-full border px-2 py-1 text-xs ${toneClass(issue.severity)}`}>{issue.severity}</span></td>
                  <td className="px-3 py-2 font-mono text-xs">{issue.code}</td>
                  <td className="px-3 py-2 text-xs text-slate-600">
                    <div>trainer: {stringify(issue.trainer_id)}</div>
                    <div>payout: {stringify(issue.payout_id)}</div>
                    <div>wallet: {stringify(issue.wallet_id)}</div>
                  </td>
                  <td className="px-3 py-2 text-xs text-slate-600">
                    <div>amount: {stringify(issue.amount ?? issue.payout_amount ?? issue.reserve_amount)}</div>
                    <div>delta: {stringify(issue.delta)}</div>
                    <div>currency: {stringify(issue.currency)}</div>
                  </td>
                  <td className="max-w-xl px-3 py-2 text-slate-700">{issue.message || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!integrityIssues.length ? <p className="p-4 text-sm text-slate-500">Payout integrity issues отсутствуют.</p> : null}
        </div>
        <p className="mt-3 text-xs text-slate-500">{state.payoutIntegrity?.actions?.note || 'Integrity endpoint is read-only.'}</p>
      </Section>

      <Section title="Repair Preview" description="Dry-run план deterministic repair: какие действия будут применены, сколько auto-repairable и сколько уйдёт в manual review.">
        <div className="mb-4 grid gap-4 md:grid-cols-4">
          <MetricCard label="Preview status" value={state.repairPreview?.summary?.status || '—'} hint={`${state.repairPreview?.summary?.issue_count ?? 0} integrity issues`} status={state.repairPreview?.summary?.status} />
          <MetricCard label="Preview actions" value={String(state.repairPreview?.summary?.preview_count ?? 0)} hint={`batch size ${repairBatchSize}`} />
          <MetricCard label="Auto repairable" value={String(state.repairPreview?.summary?.auto_repairable_count ?? 0)} hint="Eligible deterministic actions" status="healthy" />
          <MetricCard label="Manual review" value={String(state.repairPreview?.summary?.manual_review_count ?? 0)} hint={state.repairPreview?.summary?.has_more ? 'More issues after this batch' : 'Current batch'} status={state.repairPreview?.summary?.manual_review_count ? 'critical' : 'healthy'} />
        </div>

        <div className="mb-4 grid gap-4 lg:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 p-4">
            <h3 className="font-medium text-slate-900">Action codes</h3>
            <div className="mt-3 grid gap-2 text-sm text-slate-700">
              {repairActionCodes.slice(0, 8).map(([code, count]) => (
                <div className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2" key={code}>
                  <span className="font-mono text-xs">{code}</span>
                  <span className="font-semibold">{count}</span>
                </div>
              ))}
              {!repairActionCodes.length ? <span className="text-sm text-slate-500">Repair actions отсутствуют.</span> : null}
            </div>
          </div>
          <div className="rounded-2xl border border-slate-200 p-4">
            <h3 className="font-medium text-slate-900">Safety</h3>
            <dl className="mt-3 space-y-2 text-sm">
              <div className="flex justify-between gap-3"><dt className="text-slate-500">Dry run only</dt><dd>{state.repairPreview?.safety?.dry_run_only ? 'yes' : 'no'}</dd></div>
              <div className="flex justify-between gap-3"><dt className="text-slate-500">Future confirmation</dt><dd>{state.repairPreview?.safety?.requires_confirmation_for_future_execution ? 'yes' : 'no'}</dd></div>
              <div className="flex justify-between gap-3"><dt className="text-slate-500">Generated</dt><dd>{dateTime(state.repairPreview?.generated_at)}</dd></div>
            </dl>
          </div>
        </div>

        <div className="overflow-x-auto rounded-2xl border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-3 py-2">Risk</th>
                <th className="px-3 py-2">Issue</th>
                <th className="px-3 py-2">Action</th>
                <th className="px-3 py-2">Records</th>
                <th className="px-3 py-2">Amount</th>
                <th className="px-3 py-2">Message</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {repairPreviewActions.slice(0, 12).map((action, index) => (
                <tr key={`${action.issue_code}:${action.payout_id || action.wallet_id || index}`}>
                  <td className="px-3 py-2"><span className={`rounded-full border px-2 py-1 text-xs ${toneClass(action.risk_level)}`}>{action.risk_level || '—'}</span></td>
                  <td className="px-3 py-2 font-mono text-xs">{action.issue_code}</td>
                  <td className="px-3 py-2">
                    <div className="font-mono text-xs">{action.action_code}</div>
                    <div className="text-xs text-slate-500">{action.eligible_for_auto_repair ? 'auto repairable' : 'manual review'}</div>
                  </td>
                  <td className="px-3 py-2 text-xs text-slate-600">
                    <div>payout: {stringify(action.payout_id)}</div>
                    <div>wallet: {stringify(action.wallet_id)}</div>
                  </td>
                  <td className="px-3 py-2">{stringify(action.amount)} {stringify(action.currency) !== '—' ? action.currency : ''}</td>
                  <td className="max-w-xl px-3 py-2 text-slate-700">{action.message || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!repairPreviewActions.length ? <p className="p-4 text-sm text-slate-500">Repair preview пустой: текущий integrity snapshot не требует действий.</p> : null}
        </div>

        {state.lastRepairExecution ? (
          <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-950">
            Last execution: fixed {state.lastRepairExecution.summary?.repaired_count ?? 0}, skipped {state.lastRepairExecution.summary?.skipped_count ?? 0}, manual review {state.lastRepairExecution.summary?.manual_review_count ?? 0}; after status {state.lastRepairExecution.summary?.after_status || '—'}.
          </div>
        ) : null}
      </Section>

      <Section title="Repair History" description="Audit trail repair runs: operator, timestamp, changed records, result counts and manual review fallout.">
        <div className="mb-4 flex flex-wrap gap-3">
          <button className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-60" onClick={() => void runRepairAuditExport('csv')} disabled={!!busy}>
            Export repair audit CSV
          </button>
          <button className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-60" onClick={() => void runRepairAuditExport('xlsx')} disabled={!!busy}>
            Export repair audit XLSX
          </button>
        </div>
        <div className="overflow-x-auto rounded-2xl border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-3 py-2">Timestamp</th>
                <th className="px-3 py-2">Operator</th>
                <th className="px-3 py-2">Repair id</th>
                <th className="px-3 py-2">Result</th>
                <th className="px-3 py-2">Changed records</th>
                <th className="px-3 py-2">Manual review</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {state.repairAudits.slice(0, 10).map((event) => {
                const context = auditBusinessContext(event);
                const results = Array.isArray(context.results) ? (context.results as PayoutRepairExecutionResult[]) : [];
                const changed = results.filter((result) => result.status === 'repaired');
                const manual = results.filter((result) => result.status === 'manual_review_required');
                return (
                  <tr key={event.id}>
                    <td className="px-3 py-2 whitespace-nowrap">{dateTime(event.created_at)}</td>
                    <td className="px-3 py-2">{event.actor_email || event.actor || '—'}</td>
                    <td className="px-3 py-2">
                      <div className="font-mono text-xs">{event.id}</div>
                      <div className="text-xs text-slate-500">{event.entity_id}</div>
                    </td>
                    <td className="px-3 py-2 text-xs text-slate-700">
                      <div>fixed: {stringify(context.repaired_count)}</div>
                      <div>skipped: {stringify(context.skipped_count)}</div>
                      <div>manual: {stringify(context.manual_review_count)}</div>
                    </td>
                    <td className="px-3 py-2 text-xs text-slate-600">
                      {changed.slice(0, 3).map((result, index) => (
                        <div key={`${event.id}:changed:${index}`}>{result.action_code}: {repairIssueIds(result)}</div>
                      ))}
                      {!changed.length ? '—' : null}
                    </td>
                    <td className="px-3 py-2 text-xs text-slate-600">
                      {manual.slice(0, 3).map((result, index) => (
                        <div key={`${event.id}:manual:${index}`}>{result.issue_code}: {result.reason || 'manual review required'}</div>
                      ))}
                      {!manual.length ? '—' : null}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {!state.repairAudits.length ? <p className="p-4 text-sm text-slate-500">Repair execution audit events пока отсутствуют.</p> : null}
        </div>
      </Section>

      <Section title="Reconciliation snapshot" description="Read-only snapshot из /payouts/admin-ops/reconciliation/snapshot/ плюс legacy reconciliation issues.">
        <div className="mb-4 grid gap-4 md:grid-cols-3">
          <MetricCard label="Snapshot mode" value={state.adminOpsReconciliation?.mode || '—'} hint={`Generated: ${dateTime(state.adminOpsReconciliation?.generated_at)}`} />
          <MetricCard label="Snapshot status" value={state.adminOpsReconciliation?.summary?.status || '—'} hint={`${state.adminOpsReconciliation?.summary?.issue_count ?? 0} issues`} status={state.adminOpsReconciliation?.summary?.status} />
          <MetricCard label="Repair performed" value={state.adminOpsReconciliation?.actions?.repair_performed ? 'yes' : 'no'} hint="Snapshot endpoint is read-only" />
        </div>
        <div className="space-y-3">
          {(snapshotIssues.length ? snapshotIssues : state.reconciliation?.issues ?? []).slice(0, 8).map((issue, index) => (
            <div className="rounded-2xl border border-slate-200 p-4" key={`${issue.code}:${index}`}>
              <div className="flex flex-wrap items-center gap-2">
                <span className={`rounded-full border px-2 py-1 text-xs ${toneClass(issue.severity)}`}>{issue.severity}</span>
                <span className="font-medium text-slate-900">{issue.code}</span>
              </div>
              <p className="mt-2 text-sm text-slate-600">
                {issue.message || `trainer: ${issue.trainer_id || '—'}, delta: ${issue.delta || '—'}`}
              </p>
            </div>
          ))}
          {!(snapshotIssues.length || (state.reconciliation?.issues ?? []).length) ? <p className="text-sm text-slate-500">Payout reconciliation issues отсутствуют.</p> : null}
        </div>
      </Section>
    </div>
  );
}
