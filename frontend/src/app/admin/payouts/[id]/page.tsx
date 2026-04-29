'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { apiRequest, privateApi } from '@/lib/api';
import type { PayoutRequest } from '@/types/api';

function formatDate(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function pretty(value: unknown) {
  if (value === undefined || value === null || value === '') return '—';
  if (typeof value === 'string') return value;
  return JSON.stringify(value, null, 2);
}

export default function AdminPayoutDetailPage() {
  const params = useParams<{ id: string }>();
  const payoutId = useMemo(() => String(params?.id || ''), [params]);
  const { user } = useAuthSession();
  const isAdmin = user?.active_role === 'admin';
  const [item, setItem] = useState<PayoutRequest | null>(null);
  const [reason, setReason] = useState('');
  const [externalReference, setExternalReference] = useState('');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState('');

  async function load() {
    if (!payoutId) return;
    try {
      setMsg('');
      const payload = await apiRequest<PayoutRequest>(`/payouts/admin/${payoutId}/`, { auth: true });
      setItem(payload);
      setExternalReference(String(payload.metadata?.external_reference || ''));
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить payout detail');
    }
  }

  useEffect(() => {
    if (!isAdmin) return;
    void load();
  }, [isAdmin, payoutId]);

  async function transition(action: 'approve' | 'processing' | 'paid' | 'reject') {
    if (!payoutId) return;
    try {
      setBusy(true);
      setMsg('');
      const payload = await privateApi.transitionAdminPayout(payoutId, {
        action,
        external_reference: externalReference,
        reason: action === 'reject' ? reason : '',
      });
      setItem(payload);
      if (action === 'reject') setReason('');
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось обновить payout status');
    } finally {
      setBusy(false);
    }
  }

  const history = Array.isArray(item?.metadata?.ops_history) ? item?.metadata?.ops_history as Array<Record<string, unknown>> : [];

  return (
    <ProtectedPage title="Payout detail" description="Ledger, metadata и операционная история payout request.">
      {!isAdmin ? (
        <div className="card error">У текущей сессии нет admin-role.</div>
      ) : (
        <section className="stack" style={{ gap: 24 }}>
          <div className="row" style={{ alignItems: 'flex-start' }}>
            <div className="stack" style={{ gap: 10 }}>
              <span className="badge secondary">Admin finance</span>
              <h1>Payout request</h1>
              <p className="lead">{payoutId}</p>
            </div>
            <div className="inline">
              <Link href="/admin/payouts" className="button ghost">Back to payouts</Link>
              <button className="button secondary" onClick={() => void load()}>Обновить</button>
            </div>
          </div>

          {msg ? <div className="card secondary">{msg}</div> : null}

          {!item ? (
            <div className="empty-state"><h3>Заявка не загружена</h3><p>Проверь ID или права текущего пользователя.</p></div>
          ) : (
            <>
              <div className="grid-4">
                <div className="card"><div className="kpi"><span className="muted">Amount</span><strong>{item.amount || '—'} {item.currency || 'RUB'}</strong></div></div>
                <div className="card"><div className="kpi"><span className="muted">Status</span><strong>{item.status || '—'}</strong></div></div>
                <div className="card"><div className="kpi"><span className="muted">Requested</span><strong>{formatDate(item.requested_at || item.created_at)}</strong></div></div>
                <div className="card"><div className="kpi"><span className="muted">Processed</span><strong>{formatDate(item.processed_at)}</strong></div></div>
              </div>

              <div className="grid-2">
                <div className="card">
                  <h3>Transition controls</h3>
                  <div className="form" style={{ marginTop: 16 }}>
                    <div className="form-group">
                      <label className="label" htmlFor="external-ref">External reference</label>
                      <input id="external-ref" className="input" value={externalReference} onChange={(event) => setExternalReference(event.target.value)} placeholder="bank-batch-042" />
                    </div>
                    <div className="form-group">
                      <label className="label" htmlFor="reason">Reject reason</label>
                      <textarea id="reason" className="textarea" value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Неверные реквизиты" />
                    </div>
                    <div className="inline" style={{ flexWrap: 'wrap' }}>
                      <button className="button secondary" disabled={busy || item.status !== 'pending'} onClick={() => void transition('approve')}>Approve</button>
                      <button className="button secondary" disabled={busy || item.status !== 'approved'} onClick={() => void transition('processing')}>Processing</button>
                      <button className="button" disabled={busy || item.status !== 'processing'} onClick={() => void transition('paid')}>Mark paid</button>
                      <button className="button ghost" disabled={busy || item.status === 'paid' || item.status === 'rejected'} onClick={() => void transition('reject')}>Reject</button>
                    </div>
                  </div>
                </div>

                <div className="card">
                  <h3>Core fields</h3>
                  <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                    <div className="list-item"><span className="muted">Trainer ID</span><strong>{item.trainer_id || '—'}</strong></div>
                    <div className="list-item"><span className="muted">Destination</span><strong>{item.destination_masked || '—'}</strong></div>
                    <div className="list-item"><span className="muted">Approved</span><strong>{formatDate(item.approved_at)}</strong></div>
                    <div className="list-item"><span className="muted">Rejected reason</span><strong>{item.rejected_reason || '—'}</strong></div>
                  </div>
                </div>
              </div>

              <div className="grid-2">
                <div className="card">
                  <h3>Ops history</h3>
                  {history.length ? (
                    <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                      {history.map((entry, index) => (
                        <div className="list-item" key={`${entry.action}-${index}`}>
                          <span className="badge secondary">{pretty(entry.action)}</span>
                          <strong>{pretty(entry.at)}</strong>
                          <small>{pretty(entry.reason || entry.external_reference)}</small>
                        </div>
                      ))}
                    </div>
                  ) : <p className="muted">История операций пока пустая.</p>}
                </div>

                <div className="card">
                  <h3>Metadata</h3>
                  <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{pretty(item.metadata)}</pre>
                </div>
              </div>

              <div className="card">
                <h3>Ledger entries</h3>
                {item.ledger_entries?.length ? (
                  <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                    {item.ledger_entries.map((entry) => (
                      <div className="list-item" key={entry.id}>
                        <span className="badge secondary">{entry.entry_type || '—'}</span>
                        <strong>{entry.amount || '—'} {entry.currency || 'RUB'}</strong>
                        <small>{formatDate(entry.created_at)} · {pretty(entry.metadata)}</small>
                      </div>
                    ))}
                  </div>
                ) : <p className="muted">Ledger entries пока отсутствуют.</p>}
              </div>
            </>
          )}
        </section>
      )}
    </ProtectedPage>
  );
}
