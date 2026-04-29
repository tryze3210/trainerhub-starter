'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { apiRequest, privateApi } from '@/lib/api';
import type { AdminPayoutOverview, PayoutRequest } from '@/types/api';

type PayoutReconciliationIssue = {
  code: string;
  severity: string;
  trainer_id?: string;
  currency?: string;
  available_amount?: string;
  reserved_amount?: string;
  active_payout_amount?: string;
  active_payout_count?: number;
  delta?: string;
  message?: string;
};

type PayoutReconciliationReport = {
  status: 'healthy' | 'attention_required' | string;
  checked_at?: string;
  issue_count: number;
  issues: PayoutReconciliationIssue[];
};

function formatDate(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function money(value?: string | number | null, currency = 'RUB') {
  if (value === undefined || value === null || value === '') return `0 ${currency}`;
  return `${value} ${currency}`;
}

async function getReconciliation() {
  return apiRequest<PayoutReconciliationReport>('/payouts/admin/reconciliation/', { auth: true });
}

async function repairReconciliation(dryRun: boolean) {
  return apiRequest<Record<string, unknown>>('/payouts/admin/reconciliation/repair/', {
    auth: true,
    method: 'POST',
    body: JSON.stringify({ dry_run: dryRun }),
  });
}

async function bulkTransition(payload: {
  payout_ids: string[];
  action: 'approve' | 'processing' | 'paid' | 'reject';
  reason?: string;
  external_reference?: string;
}) {
  return apiRequest<{ results: Array<{ id: string; ok: boolean; status?: string; error?: unknown }> }>('/payouts/admin/bulk-transition/', {
    auth: true,
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export default function AdminPayoutsPage() {
  const { user } = useAuthSession();
  const isAdmin = user?.active_role === 'admin';
  const [items, setItems] = useState<PayoutRequest[]>([]);
  const [overview, setOverview] = useState<AdminPayoutOverview | null>(null);
  const [reconciliation, setReconciliation] = useState<PayoutReconciliationReport | null>(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [externalReference, setExternalReference] = useState('');
  const [reason, setReason] = useState('');
  const [selected, setSelected] = useState<string[]>([]);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [busyOperation, setBusyOperation] = useState<string | null>(null);
  const [msg, setMsg] = useState('');

  async function load() {
    try {
      setMsg('');
      const [payload, overviewPayload, reconciliationPayload] = await Promise.all([
        privateApi.listAdminPayouts(statusFilter || undefined),
        privateApi.getAdminPayoutOverview(),
        getReconciliation(),
      ]);
      setItems(payload);
      setOverview(overviewPayload);
      setReconciliation(reconciliationPayload);
      setSelected((current) => current.filter((id) => payload.some((item) => item.id === id)));
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить payout queue');
    }
  }

  useEffect(() => {
    if (!isAdmin) return;
    void load();
  }, [isAdmin, statusFilter]);

  const stats = useMemo(() => {
    const buckets = new Map((overview?.statuses || []).map((bucket) => [bucket.status, bucket]));
    const fallbackPending = items.filter((item) => item.status === 'pending').length;
    const fallbackProcessing = items.filter((item) => item.status === 'approved' || item.status === 'processing').length;
    const fallbackRejected = items.filter((item) => item.status === 'rejected').length;
    const total = overview?.statuses.reduce((acc, bucket) => acc + bucket.count, 0) ?? items.length;

    return {
      pending: buckets.get('pending')?.count ?? fallbackPending,
      processing: (buckets.get('approved')?.count ?? 0) + (buckets.get('processing')?.count ?? fallbackProcessing),
      rejected: buckets.get('rejected')?.count ?? fallbackRejected,
      total,
    };
  }, [items, overview]);

  function toggleSelected(id: string) {
    setSelected((current) => (current.includes(id) ? current.filter((value) => value !== id) : [...current, id]));
  }

  async function transition(id: string, action: 'approve' | 'processing' | 'paid' | 'reject') {
    try {
      setBusyId(id);
      setMsg('');
      await privateApi.transitionAdminPayout(id, {
        action,
        external_reference: externalReference,
        reason: action === 'reject' ? reason : '',
      });
      if (action === 'reject') setReason('');
      await load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось обновить payout status');
    } finally {
      setBusyId(null);
    }
  }

  async function runBulk(action: 'approve' | 'processing' | 'paid' | 'reject') {
    if (!selected.length) {
      setMsg('Выбери хотя бы одну payout заявку.');
      return;
    }
    try {
      setBusyOperation(`bulk-${action}`);
      setMsg('');
      const result = await bulkTransition({
        payout_ids: selected,
        action,
        external_reference: externalReference,
        reason: action === 'reject' ? reason : '',
      });
      const failed = result.results.filter((item) => !item.ok).length;
      setMsg(failed ? `Bulk ${action}: ${failed} ошибок из ${result.results.length}.` : `Bulk ${action}: выполнено ${result.results.length}.`);
      setSelected([]);
      await load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Bulk operation failed');
    } finally {
      setBusyOperation(null);
    }
  }

  async function runRepair(dryRun: boolean) {
    try {
      setBusyOperation(dryRun ? 'repair-dry' : 'repair-apply');
      setMsg('');
      const result = await repairReconciliation(dryRun);
      const repairedCount = Number(result.repaired_count || 0);
      setMsg(dryRun ? 'Dry-run reconciliation выполнен.' : `Reconciliation repair применен. Исправлено: ${repairedCount}.`);
      await load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Reconciliation repair failed');
    } finally {
      setBusyOperation(null);
    }
  }

  return (
    <ProtectedPage title="Admin payouts" description="Очередь payout request, reconciliation и ручная обработка выплат.">
      {!isAdmin ? (
        <div className="card error">У текущей сессии нет admin-role.</div>
      ) : (
        <section className="stack" style={{ gap: 24 }}>
          <div className="row" style={{ alignItems: 'flex-start' }}>
            <div className="stack" style={{ gap: 10 }}>
              <span className="badge secondary">Admin finance</span>
              <h1>Операции выплат</h1>
              <p className="lead">Approve / processing / paid / reject, reserve-ledger, reconciliation и bulk-операции.</p>
            </div>
            <div className="inline">
              <Link href="/admin" className="button ghost">Admin cockpit</Link>
              <button className="button secondary" onClick={() => void load()}>Обновить</button>
            </div>
          </div>

          {msg ? <div className="card secondary">{msg}</div> : null}

          <div className="grid-4">
            <div className="card"><div className="kpi"><span className="muted">Pending exposure</span><strong>{money(overview?.ops.pending_exposure_amount)}</strong><small>{overview?.ops.pending_exposure_count ?? stats.pending} заявок</small></div></div>
            <div className="card"><div className="kpi"><span className="muted">Reserved</span><strong>{money(overview?.ops.reserved_amount)}</strong><small>hold под выплаты</small></div></div>
            <div className="card"><div className="kpi"><span className="muted">Available</span><strong>{money(overview?.ops.available_amount)}</strong><small>доступно тренерам</small></div></div>
            <div className={reconciliation?.status === 'healthy' ? 'card' : 'card warning'}><div className="kpi"><span className="muted">Reconciliation</span><strong>{reconciliation?.status || '—'}</strong><small>{reconciliation?.issue_count ?? 0} issues</small></div></div>
          </div>

          <div className="grid-4">
            <div className="card"><div className="kpi"><span className="muted">Pending</span><strong>{stats.pending}</strong></div></div>
            <div className="card"><div className="kpi"><span className="muted">In progress</span><strong>{stats.processing}</strong></div></div>
            <div className="card"><div className="kpi"><span className="muted">Rejected</span><strong>{stats.rejected}</strong></div></div>
            <div className="card"><div className="kpi"><span className="muted">Всего</span><strong>{stats.total}</strong></div></div>
          </div>

          <div className="grid-2">
            <div className="card">
              <h3>Фильтр и processing meta</h3>
              <div className="form" style={{ marginTop: 16 }}>
                <div className="form-group">
                  <label className="label" htmlFor="admin-payout-status">Статус</label>
                  <select id="admin-payout-status" className="select" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                    <option value="">Все</option>
                    <option value="pending">pending</option>
                    <option value="approved">approved</option>
                    <option value="processing">processing</option>
                    <option value="paid">paid</option>
                    <option value="rejected">rejected</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="label" htmlFor="admin-payout-reference">External reference</label>
                  <input id="admin-payout-reference" className="input" value={externalReference} onChange={(event) => setExternalReference(event.target.value)} placeholder="bank-batch-042" />
                </div>
                <div className="form-group">
                  <label className="label" htmlFor="admin-payout-reason">Reject reason</label>
                  <textarea id="admin-payout-reason" className="textarea" value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Неверные реквизиты" />
                </div>
              </div>
            </div>

            <div className="card">
              <h3>Reconciliation control</h3>
              <div className="stack" style={{ gap: 12, marginTop: 16 }}>
                <p className="muted">Сверяет reserved balance с суммой payout заявок в статусах pending / approved / processing.</p>
                <div className="inline" style={{ flexWrap: 'wrap' }}>
                  <button className="button secondary" disabled={busyOperation === 'repair-dry'} onClick={() => void runRepair(true)}>Dry-run repair</button>
                  <button className="button" disabled={busyOperation === 'repair-apply'} onClick={() => void runRepair(false)}>Apply safe repair</button>
                </div>
                {reconciliation?.issues?.length ? (
                  <div className="stack" style={{ gap: 8 }}>
                    {reconciliation.issues.slice(0, 4).map((issue, index) => (
                      <div className="list-item" key={`${issue.code}-${issue.trainer_id}-${index}`}>
                        <span className="badge secondary">{issue.severity}</span>
                        <strong>{issue.code}</strong>
                        <small>{issue.message || '—'}</small>
                      </div>
                    ))}
                  </div>
                ) : <p className="muted">Расхождений нет.</p>}
              </div>
            </div>
          </div>

          <div className="card">
            <div className="row">
              <div>
                <h3>Bulk actions</h3>
                <p className="muted">Выбрано заявок: {selected.length}. Bulk-операции используют ту же строгую state-machine.</p>
              </div>
              <div className="inline" style={{ flexWrap: 'wrap' }}>
                <button className="button secondary" disabled={!selected.length || !!busyOperation} onClick={() => void runBulk('approve')}>Approve selected</button>
                <button className="button secondary" disabled={!selected.length || !!busyOperation} onClick={() => void runBulk('processing')}>Processing selected</button>
                <button className="button" disabled={!selected.length || !!busyOperation} onClick={() => void runBulk('paid')}>Paid selected</button>
                <button className="button ghost" disabled={!selected.length || !!busyOperation} onClick={() => void runBulk('reject')}>Reject selected</button>
              </div>
            </div>
          </div>

          {overview?.ledger?.length ? (
            <div className="card">
              <h3>Ledger snapshot</h3>
              <div className="grid-4" style={{ marginTop: 16 }}>
                {overview.ledger.map((bucket) => (
                  <div className="list-item" key={bucket.entry_type}>
                    <span className="muted">{bucket.entry_type}</span>
                    <strong>{money(bucket.amount)}</strong>
                    <small>{bucket.count} записей</small>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {items.length === 0 ? (
            <div className="empty-state"><h3>Очередь пуста</h3><p>Нет payout request под выбранный фильтр.</p></div>
          ) : (
            <div className="grid-2">
              {items.map((item) => (
                <article className="card" key={item.id}>
                  <div className="stack" style={{ gap: 12 }}>
                    <div className="row">
                      <label className="inline" style={{ gap: 8 }}>
                        <input type="checkbox" checked={selected.includes(item.id)} onChange={() => toggleSelected(item.id)} />
                        <strong>{item.amount || '—'} {item.currency || 'RUB'}</strong>
                      </label>
                      <span className="badge secondary">{item.status || '—'}</span>
                    </div>
                    <div className="grid-2">
                      <div className="list-item"><span className="muted">Trainer</span><strong>{item.trainer_id || '—'}</strong></div>
                      <div className="list-item"><span className="muted">Requested</span><strong>{formatDate(item.requested_at || item.created_at)}</strong></div>
                      <div className="list-item"><span className="muted">Destination</span><strong>{item.destination_masked || '—'}</strong></div>
                      <div className="list-item"><span className="muted">Reference</span><strong>{String(item.metadata?.external_reference || '—')}</strong></div>
                    </div>
                    {item.rejected_reason ? <div className="card compact error">Reject reason: {item.rejected_reason}</div> : null}
                    <div className="inline" style={{ flexWrap: 'wrap' }}>
                      <button className="button secondary" disabled={busyId === item.id || item.status !== 'pending'} onClick={() => void transition(item.id, 'approve')}>Approve</button>
                      <button className="button secondary" disabled={busyId === item.id || item.status !== 'approved'} onClick={() => void transition(item.id, 'processing')}>Processing</button>
                      <button className="button" disabled={busyId === item.id || item.status !== 'processing'} onClick={() => void transition(item.id, 'paid')}>Mark paid</button>
                      <button className="button ghost" disabled={busyId === item.id || item.status === 'paid' || item.status === 'rejected'} onClick={() => void transition(item.id, 'reject')}>Reject</button>
                      <Link href={`/admin/payouts/${item.id}`} className="button ghost">Detail</Link>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      )}
    </ProtectedPage>
  );
}
