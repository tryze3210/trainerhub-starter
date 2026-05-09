'use client';

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';

import { useAuthSession } from '@/components/auth-provider';
import { adminPayoutsApi, type AdminPayoutLedgerEntry, type AdminPayoutRequest } from '@/modules/admin-payouts/api';

function money(value: string | number | null | undefined, currency = 'RUB') {
  const amount = Number(value ?? 0);
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency, maximumFractionDigits: 2 }).format(Number.isFinite(amount) ? amount : 0);
}

function dateTime(value: string | null | undefined) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('ru-RU');
}

function prettyJson(value: unknown) {
  if (!value || typeof value !== 'object') return '—';
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function statusTone(status: string | undefined) {
  if (!status) return 'secondary';
  if (status === 'paid') return 'success';
  if (status === 'rejected') return 'danger';
  if (status === 'approved' || status === 'processing') return 'warning';
  return 'secondary';
}

function LedgerTable({ entries }: { entries: AdminPayoutLedgerEntry[] }) {
  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>Created</th>
            <th>Type</th>
            <th>Amount</th>
            <th>Payment</th>
            <th>Metadata</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr key={entry.id}>
              <td>{dateTime(entry.created_at)}</td>
              <td>{entry.entry_type}</td>
              <td>{money(entry.amount, entry.currency)}</td>
              <td>{entry.payment_id || '—'}</td>
              <td><pre className="code-inline">{prettyJson(entry.metadata)}</pre></td>
            </tr>
          ))}
          {!entries.length ? <tr><td colSpan={5}>Ledger entries не найдены.</td></tr> : null}
        </tbody>
      </table>
    </div>
  );
}

export function AdminPayoutDetailPage({ payoutId }: { payoutId: string }) {
  const { user } = useAuthSession();
  const isAdmin = user?.active_role === 'admin';
  const [payout, setPayout] = useState<AdminPayoutRequest | null>(null);
  const [externalReference, setExternalReference] = useState('');
  const [rejectReason, setRejectReason] = useState('');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState('');
  const [message, setMessage] = useState('');

  const load = useCallback(async () => {
    if (!isAdmin || !payoutId) return;
    setLoading(true);
    setMessage('');
    try {
      setPayout(await adminPayoutsApi.getPayout(payoutId));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Не удалось загрузить payout detail');
    } finally {
      setLoading(false);
    }
  }, [isAdmin, payoutId]);

  useEffect(() => {
    void load();
  }, [load]);

  const transition = async (action: 'approve' | 'processing' | 'paid' | 'reject') => {
    if (!payout) return;
    if (action === 'reject' && !rejectReason.trim()) {
      setMessage('Reject reason обязателен.');
      return;
    }
    setBusy(action);
    setMessage('');
    try {
      if (action === 'approve') await adminPayoutsApi.approve(payout.id, { external_reference: externalReference });
      if (action === 'processing') await adminPayoutsApi.markProcessing(payout.id, { external_reference: externalReference });
      if (action === 'paid') await adminPayoutsApi.markPaid(payout.id, { external_reference: externalReference });
      if (action === 'reject') await adminPayoutsApi.reject(payout.id, { reason: rejectReason.trim(), external_reference: externalReference });
      setMessage(`Payout ${action} выполнен.`);
      await load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : `Payout ${action} не выполнен`);
    } finally {
      setBusy('');
    }
  };

  if (!isAdmin) return <section className="card danger">У текущей сессии нет admin-role.</section>;
  if (loading && !payout) return <section className="card">Загружаем payout detail…</section>;

  return (
    <section className="stack gap-lg">
      <div className="row between wrap gap-md">
        <div>
          <span className="eyebrow">Admin payout detail</span>
          <h1>Payout request</h1>
          <p className="muted">{payoutId}</p>
        </div>
        <div className="inline wrap gap-sm">
          <Link className="btn ghost" href="/admin/payouts">Назад к выплатам</Link>
          <button className="btn" type="button" onClick={() => void load()} disabled={loading}>Обновить</button>
        </div>
      </div>

      {message ? <div className="card warning">{message}</div> : null}

      {payout ? (
        <>
          <div className="grid-4">
            <article className="card stack"><span className="muted">Amount</span><strong className="stat-value">{money(payout.amount, payout.currency)}</strong></article>
            <article className="card stack"><span className="muted">Status</span><strong><span className={`badge ${statusTone(payout.status)}`}>{payout.status}</span></strong></article>
            <article className="card stack"><span className="muted">Trainer</span><strong>{payout.trainer_id || '—'}</strong></article>
            <article className="card stack"><span className="muted">Wallet</span><strong>{payout.wallet_id || '—'}</strong></article>
          </div>

          <div className="grid-2">
            <article className="card stack">
              <h2>Lifecycle</h2>
              <dl className="stack gap-xs">
                <div><dt>Requested</dt><dd>{dateTime(payout.requested_at || payout.created_at)}</dd></div>
                <div><dt>Approved</dt><dd>{dateTime(payout.approved_at)}</dd></div>
                <div><dt>Processed</dt><dd>{dateTime(payout.processed_at)}</dd></div>
                <div><dt>Destination</dt><dd>{payout.destination_masked || '—'}</dd></div>
                <div><dt>Rejected reason</dt><dd>{payout.rejected_reason || '—'}</dd></div>
              </dl>
            </article>

            <article className="card stack">
              <h2>Manual actions</h2>
              <label className="field">
                External reference
                <input value={externalReference} onChange={(event) => setExternalReference(event.target.value)} placeholder="bank-batch-042" />
              </label>
              <label className="field">
                Reject reason
                <input value={rejectReason} onChange={(event) => setRejectReason(event.target.value)} placeholder="Неверные реквизиты" />
              </label>
              <div className="inline wrap gap-sm">
                <button className="btn ghost" type="button" onClick={() => void transition('approve')} disabled={!!busy || !(payout.status === 'pending' || payout.status === 'requested')}>Approve</button>
                <button className="btn ghost" type="button" onClick={() => void transition('processing')} disabled={!!busy || payout.status !== 'approved'}>Processing</button>
                <button className="btn" type="button" onClick={() => void transition('paid')} disabled={!!busy || !(payout.status === 'processing' || payout.status === 'approved')}>Mark paid</button>
                <button className="btn danger" type="button" onClick={() => void transition('reject')} disabled={!!busy || payout.status === 'paid' || payout.status === 'rejected'}>Reject</button>
              </div>
            </article>
          </div>

          <article className="card stack">
            <h2>Ledger entries</h2>
            <LedgerTable entries={payout.ledger_entries ?? []} />
          </article>

          <article className="card stack">
            <h2>Raw metadata</h2>
            <pre>{prettyJson(payout.metadata)}</pre>
          </article>
        </>
      ) : null}
    </section>
  );
}
