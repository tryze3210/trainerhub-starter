'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { useAuthSession } from '@/components/auth-provider';
import {
  adminPayoutsApi,
  type AdminPayoutOverview,
  type AdminPayoutProjectionHealth,
  type AdminPayoutRequest,
  type AdminPayoutRiskHold,
  type AdminPayoutRiskHoldSummary,
  type PayoutReconciliationReport,
} from '@/modules/admin-payouts/api';

type DashboardState = {
  overview: AdminPayoutOverview | null;
  payouts: AdminPayoutRequest[];
  reconciliation: PayoutReconciliationReport | null;
  riskSummary: AdminPayoutRiskHoldSummary | null;
  riskHolds: AdminPayoutRiskHold[];
  projection: AdminPayoutProjectionHealth | null;
};

type PayoutAction = 'approve' | 'processing' | 'paid' | 'reject';

const STATUS_OPTIONS = ['', 'pending', 'approved', 'processing', 'paid', 'rejected'];

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

function statusTone(status: string | undefined) {
  if (!status) return 'secondary';
  if (['paid', 'healthy', 'ok'].includes(status)) return 'success';
  if (['rejected', 'failed', 'critical'].includes(status)) return 'danger';
  if (['processing', 'approved', 'attention_required', 'degraded'].includes(status)) return 'warning';
  return 'secondary';
}

function MetricCard({ label, value, hint, tone }: { label: string; value: string; hint?: string; tone?: string }) {
  return (
    <article className={`card stack ${tone || ''}`}>
      <span className="muted">{label}</span>
      <strong className="stat-value">{value}</strong>
      {hint ? <span className="muted">{hint}</span> : null}
    </article>
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

export function AdminPayoutOperationsDashboard() {
  const { user } = useAuthSession();
  const isAdmin = user?.active_role === 'admin';
  const [state, setState] = useState<DashboardState>({
    overview: null,
    payouts: [],
    reconciliation: null,
    riskSummary: null,
    riskHolds: [],
    projection: null,
  });
  const [statusFilter, setStatusFilter] = useState('');
  const [trainerFilter, setTrainerFilter] = useState('');
  const [externalReference, setExternalReference] = useState('');
  const [rejectReason, setRejectReason] = useState('');
  const [releaseReason, setReleaseReason] = useState('manual_admin_release');
  const [selected, setSelected] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState('');

  const load = useCallback(async () => {
    if (!isAdmin) return;
    setLoading(true);
    setMessage('');
    try {
      const [overview, payouts, reconciliation, riskSummary, riskHolds, projection] = await Promise.all([
        adminPayoutsApi.getOverview(),
        adminPayoutsApi.listPayouts({ status: statusFilter || undefined, trainer_id: trainerFilter || undefined, limit: 100 }),
        adminPayoutsApi.getReconciliation(),
        adminPayoutsApi.getRiskHoldSummary(50),
        adminPayoutsApi.listRiskHolds({ trainer_id: trainerFilter || undefined, limit: 50 }),
        adminPayoutsApi.getProjectionHealth(),
      ]);
      setState({ overview, payouts, reconciliation, riskSummary, riskHolds, projection });
      setSelected((current) => current.filter((id) => payouts.some((payout) => payout.id === id)));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Не удалось загрузить admin payout operations');
    } finally {
      setLoading(false);
    }
  }, [isAdmin, statusFilter, trainerFilter]);

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

  const toggleSelected = (payoutId: string) => {
    setSelected((current) => (current.includes(payoutId) ? current.filter((value) => value !== payoutId) : [...current, payoutId]));
  };

  if (!isAdmin) {
    return <section className="card danger">У текущей сессии нет admin-role.</section>;
  }

  return (
    <section className="stack gap-lg">
      <div className="row between wrap gap-md">
        <div className="stack gap-xs">
          <span className="eyebrow">Admin finance operations</span>
          <h1>Операции выплат</h1>
          <p className="muted">Approve / processing / mark-paid / reject, risk holds, payout projection и reconciliation repair.</p>
        </div>
        <div className="inline wrap gap-sm">
          <Link className="btn ghost" href="/admin/operations">Operations hub</Link>
          <button className="btn" type="button" onClick={() => void load()} disabled={loading}>Обновить</button>
        </div>
      </div>

      {message ? <div className="card warning">{message}</div> : null}
      {loading && state.payouts.length === 0 ? <div className="card">Загружаем payout operations…</div> : null}

      <div className="grid-4">
        <MetricCard label="Pending exposure" value={money(state.overview?.ops.pending_exposure_amount)} hint={`${state.overview?.ops.pending_exposure_count ?? stats.pending} заявок`} />
        <MetricCard label="Reserved balance" value={money(state.overview?.ops.reserved_amount)} hint="locked под активные выплаты" />
        <MetricCard label="Risk holds" value={money(state.riskSummary?.active_hold_amount)} hint={`${state.riskSummary?.active_hold_count ?? 0} active holds`} tone={state.riskSummary?.active_hold_count ? 'warning' : ''} />
        <MetricCard label="Reconciliation" value={state.reconciliation?.status || '—'} hint={`${state.reconciliation?.issue_count ?? 0} issues`} tone={statusTone(state.reconciliation?.status)} />
      </div>

      <div className="grid-5">
        <MetricCard label="Pending" value={String(stats.pending)} />
        <MetricCard label="Approved" value={String(stats.approved)} />
        <MetricCard label="Processing" value={String(stats.processing)} />
        <MetricCard label="Paid" value={String(stats.paid)} />
        <MetricCard label="Rejected" value={String(stats.rejected)} />
      </div>

      <div className="grid-2">
        <article className="card stack">
          <h2>Фильтры и meta</h2>
          <label className="field">
            Статус
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              {STATUS_OPTIONS.map((status) => <option key={status || 'all'} value={status}>{status || 'Все'}</option>)}
            </select>
          </label>
          <label className="field">
            Trainer id
            <input value={trainerFilter} onChange={(event) => setTrainerFilter(event.target.value)} placeholder="user_id или trainer profile id" />
          </label>
          <label className="field">
            External reference
            <input value={externalReference} onChange={(event) => setExternalReference(event.target.value)} placeholder="bank-batch-042" />
          </label>
          <label className="field">
            Reject reason
            <input value={rejectReason} onChange={(event) => setRejectReason(event.target.value)} placeholder="Неверные реквизиты" />
          </label>
        </article>

        <article className="card stack">
          <h2>Ops controls</h2>
          <p className="muted">Все действия идут через backend state-machine и пишут audit events.</p>
          <div className="inline wrap gap-sm">
            <button className="btn ghost" type="button" onClick={() => void runProjectOutbox()} disabled={!!busy}>Project outbox</button>
            <button className="btn ghost" type="button" onClick={() => void runReconciliationRepair(true)} disabled={!!busy}>Dry-run repair</button>
            <button className="btn" type="button" onClick={() => void runReconciliationRepair(false)} disabled={!!busy}>Apply repair</button>
          </div>
          <div className="list-item">
            <span className={`badge ${statusTone(state.projection?.status)}`}>{state.projection?.status || 'projection —'}</span>
            <strong>{state.projection?.consumer || 'payout projection'}</strong>
            <small>projected: {state.projection?.projected_messages ?? 0}, failed: {state.projection?.failed_messages ?? 0}</small>
          </div>
        </article>
      </div>

      <article className="card stack">
        <div className="row between wrap gap-md">
          <div>
            <h2>Bulk actions</h2>
            <p className="muted">Выбрано payout requests: {selected.length}. Bulk reject требует reason.</p>
          </div>
          <div className="inline wrap gap-sm">
            <button className="btn ghost" type="button" onClick={() => void runBulk('approve')} disabled={!selected.length || !!busy}>Approve selected</button>
            <button className="btn ghost" type="button" onClick={() => void runBulk('processing')} disabled={!selected.length || !!busy}>Processing selected</button>
            <button className="btn" type="button" onClick={() => void runBulk('paid')} disabled={!selected.length || !!busy}>Paid selected</button>
            <button className="btn danger" type="button" onClick={() => void runBulk('reject')} disabled={!selected.length || !!busy}>Reject selected</button>
          </div>
        </div>
      </article>

      <article className="card stack">
        <h2>Payout queue</h2>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th></th>
                <th>Created</th>
                <th>Trainer</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Destination</th>
                <th>Next</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {state.payouts.map((payout) => (
                <tr key={payout.id}>
                  <td><input type="checkbox" checked={selected.includes(payout.id)} onChange={() => toggleSelected(payout.id)} /></td>
                  <td>{dateTime(payout.requested_at || payout.created_at)}</td>
                  <td>{payout.trainer_id || '—'}</td>
                  <td>{money(payout.amount, payout.currency)}</td>
                  <td><span className={`badge ${statusTone(payout.status)}`}>{payout.status}</span></td>
                  <td>{payout.destination_masked || '—'}</td>
                  <td>{nextHint(payout)}</td>
                  <td>
                    <div className="inline wrap gap-xs">
                      {(['approve', 'processing', 'paid', 'reject'] as PayoutAction[]).map((action) => (
                        <button
                          className={action === 'reject' ? 'btn danger compact' : 'btn ghost compact'}
                          type="button"
                          key={action}
                          disabled={!actionAllowed(payout, action) || busy === `${action}:${payout.id}`}
                          onClick={() => void runAction(payout, action)}
                        >
                          {actionLabel(action)}
                        </button>
                      ))}
                      <Link className="btn ghost compact" href={`/admin/payouts/${payout.id}`}>Detail</Link>
                    </div>
                  </td>
                </tr>
              ))}
              {!state.payouts.length ? (
                <tr><td colSpan={8}>Нет payout requests под выбранный фильтр.</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </article>

      <div className="grid-2">
        <article className="card stack">
          <h2>Risk holds</h2>
          <label className="field">
            Release reason
            <input value={releaseReason} onChange={(event) => setReleaseReason(event.target.value)} />
          </label>
          <div className="stack gap-sm">
            {state.riskHolds.slice(0, 8).map((hold) => (
              <div className="list-item" key={hold.id}>
                <div className="row between wrap gap-sm">
                  <div>
                    <span className={`badge ${statusTone(hold.status)}`}>{hold.status}</span>
                    <strong>{money(hold.active_amount ?? hold.amount, hold.currency)}</strong>
                    <small>payment: {hold.payment_id || '—'} · trainer: {hold.trainer_id || '—'}</small>
                  </div>
                  <button className="btn ghost compact" type="button" onClick={() => void releaseHold(hold)} disabled={!hold.payment_id || busy === `hold:${hold.id}`}>
                    Release
                  </button>
                </div>
              </div>
            ))}
            {!state.riskHolds.length ? <p className="muted">Active risk holds не найдены.</p> : null}
          </div>
        </article>

        <article className="card stack">
          <h2>Reconciliation issues</h2>
          {(state.reconciliation?.issues ?? []).slice(0, 8).map((issue, index) => (
            <div className="list-item" key={`${issue.code}-${issue.trainer_id || index}`}>
              <span className={`badge ${statusTone(issue.severity)}`}>{issue.severity}</span>
              <strong>{issue.code}</strong>
              <small>{issue.message || `trainer: ${issue.trainer_id || '—'}, delta: ${issue.delta || '—'}`}</small>
            </div>
          ))}
          {!(state.reconciliation?.issues ?? []).length ? <p className="muted">Payout reconciliation issues отсутствуют.</p> : null}
        </article>
      </div>
    </section>
  );
}
