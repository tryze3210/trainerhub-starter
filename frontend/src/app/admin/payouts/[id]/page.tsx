'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { isAdminUser } from '@/lib/authz';
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
  const isAdmin = isAdminUser(user);
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
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить детали выплаты');
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
      setMsg(err instanceof Error ? err.message : 'Не удалось обновить статус выплаты');
    } finally {
      setBusy(false);
    }
  }

  const history = Array.isArray(item?.metadata?.ops_history) ? item?.metadata?.ops_history as Array<Record<string, unknown>> : [];

  return (
    <ProtectedPage title="Детали выплаты" description="Реестр, метаданные и операционная история заявки на выплату.">
      {!isAdmin ? (
        <div className="card error">У текущей сессии нет роли администратора.</div>
      ) : (
        <section className="stack" style={{ gap: 24 }}>
          <div className="row" style={{ alignItems: 'flex-start' }}>
            <div className="stack" style={{ gap: 10 }}>
              <span className="badge secondary">Финансы администратора</span>
              <h1>Заявка на выплату</h1>
              <p className="lead">{payoutId}</p>
            </div>
            <div className="inline">
              <Link href="/admin/payouts" className="button ghost">Назад к выплатам</Link>
              <button className="button secondary" onClick={() => void load()}>Обновить</button>
            </div>
          </div>

          {msg ? <div className="card secondary">{msg}</div> : null}

          {!item ? (
            <div className="empty-state"><h3>Заявка не загружена</h3><p>Проверь ID или права текущего пользователя.</p></div>
          ) : (
            <>
              <div className="grid-4">
                <div className="card"><div className="kpi"><span className="muted">Сумма</span><strong>{item.amount || '—'} {item.currency || 'RUB'}</strong></div></div>
                <div className="card"><div className="kpi"><span className="muted">Статус</span><strong>{item.status || '—'}</strong></div></div>
                <div className="card"><div className="kpi"><span className="muted">Запрошено</span><strong>{formatDate(item.requested_at || item.created_at)}</strong></div></div>
                <div className="card"><div className="kpi"><span className="muted">Обработано</span><strong>{formatDate(item.processed_at)}</strong></div></div>
              </div>

              <div className="grid-2">
                <div className="card">
                  <h3>Управление статусом</h3>
                  <div className="form" style={{ marginTop: 16 }}>
                    <div className="form-group">
                      <label className="label" htmlFor="external-ref">Внешняя ссылка</label>
                      <input id="external-ref" className="input" value={externalReference} onChange={(event) => setExternalReference(event.target.value)} placeholder="bank-batch-042" />
                    </div>
                    <div className="form-group">
                      <label className="label" htmlFor="reason">Причина отклонения</label>
                      <textarea id="reason" className="textarea" value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Неверные реквизиты" />
                    </div>
                    <div className="inline" style={{ flexWrap: 'wrap' }}>
                      <button className="button secondary" disabled={busy || item.status !== 'pending'} onClick={() => void transition('approve')}>Одобрить</button>
                      <button className="button secondary" disabled={busy || item.status !== 'approved'} onClick={() => void transition('processing')}>В обработку</button>
                      <button className="button" disabled={busy || item.status !== 'processing'} onClick={() => void transition('paid')}>Отметить оплаченной</button>
                      <button className="button ghost" disabled={busy || item.status === 'paid' || item.status === 'rejected'} onClick={() => void transition('reject')}>Отклонить</button>
                    </div>
                  </div>
                </div>

                <div className="card">
                  <h3>Основные поля</h3>
                  <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                    <div className="list-item"><span className="muted">ID тренера</span><strong>{item.trainer_id || '—'}</strong></div>
                    <div className="list-item"><span className="muted">Получатель</span><strong>{item.destination_masked || '—'}</strong></div>
                    <div className="list-item"><span className="muted">Одобрено</span><strong>{formatDate(item.approved_at)}</strong></div>
                    <div className="list-item"><span className="muted">Причина отклонения</span><strong>{item.rejected_reason || '—'}</strong></div>
                  </div>
                </div>
              </div>

              <div className="grid-2">
                <div className="card">
                  <h3>История операций</h3>
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
                  <h3>Метаданные</h3>
                  <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{pretty(item.metadata)}</pre>
                </div>
              </div>

              <div className="card">
                <h3>Записи реестра</h3>
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
                ) : <p className="muted">Записи реестра пока отсутствуют.</p>}
              </div>
            </>
          )}
        </section>
      )}
    </ProtectedPage>
  );
}
