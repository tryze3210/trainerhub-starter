'use client';

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';

import { useAuthSession } from '@/components/auth-provider';
import { isAdminUser } from '@/lib/authz';
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

function eligibilityReasonText(reason: string | undefined) {
  if (!reason) return 'Ограничений нет';
  const labels: Record<string, string> = {
    kyc_profile_missing: 'Не заполнена анкета KYC',
    kyc_not_approved: 'KYC не одобрен',
    payout_profile_incomplete: 'Не заполнены юридические данные для выплат',
    active_trainer_agreement_missing: 'Нет активного договора тренера',
  };
  return reason
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item) => labels[item] || item)
    .join(', ');
}

function kycStatusText(status: string | undefined) {
  if (status === 'approved') return 'Одобрен';
  if (status === 'pending') return 'На проверке';
  if (status === 'rejected') return 'Отклонен';
  if (status === 'draft') return 'Черновик';
  return status || 'Нет анкеты';
}

function LedgerTable({ entries }: { entries: AdminPayoutLedgerEntry[] }) {
  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>Создано</th>
            <th>Тип</th>
            <th>Сумма</th>
            <th>Платеж</th>
            <th>Метаданные</th>
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
          {!entries.length ? <tr><td colSpan={5}>Записи ledger не найдены.</td></tr> : null}
        </tbody>
      </table>
    </div>
  );
}

export function AdminPayoutDetailPage({ payoutId }: { payoutId: string }) {
  const { user } = useAuthSession();
  const isAdmin = isAdminUser(user);
  const [payout, setPayout] = useState<AdminPayoutRequest | null>(null);
  const [externalReference, setExternalReference] = useState('');
  const [rejectReason, setОтклонитьReason] = useState('');
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
    if (action !== 'reject' && payout.payout_eligibility && !payout.payout_eligibility.is_eligible) {
      setMessage(`Выплата заблокирована: ${eligibilityReasonText(payout.payout_eligibility.block_reason)}.`);
      return;
    }
    if (action === 'reject' && !rejectReason.trim()) {
      setMessage('Отклонить reason обязателен.');
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

  if (!isAdmin) return <section className="card danger">У текущей сессии нет прав администратора.</section>;
  if (loading && !payout) return <section className="card">Загружаем детали выплаты…</section>;

  return (
    <section className="stack gap-lg">
      <div className="row between wrap gap-md">
        <div>
          <span className="eyebrow">Детали выплаты</span>
          <h1>Заявка на выплату</h1>
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
          {payout.payout_eligibility && !payout.payout_eligibility.is_eligible ? (
            <div className="card danger">
              Выплата заблокирована: {eligibilityReasonText(payout.payout_eligibility.block_reason)}.
            </div>
          ) : null}

          <div className="grid-4">
            <article className="card stack"><span className="muted">Сумма</span><strong className="stat-value">{money(payout.amount, payout.currency)}</strong></article>
            <article className="card stack"><span className="muted">Статус</span><strong><span className={`badge ${statusTone(payout.status)}`}>{payout.status}</span></strong></article>
            <article className="card stack"><span className="muted">Тренер</span><strong>{payout.trainer_id || '—'}</strong></article>
            <article className="card stack"><span className="muted">Кошелек</span><strong>{payout.wallet_id || '—'}</strong></article>
          </div>

          <div className="grid-2">
            <article className="card stack">
              <h2>Жизненный цикл</h2>
              <dl className="stack gap-xs">
                <div><dt>Запрошено</dt><dd>{dateTime(payout.requested_at || payout.created_at)}</dd></div>
                <div><dt>Одобрено</dt><dd>{dateTime(payout.approved_at)}</dd></div>
                <div><dt>Обработано</dt><dd>{dateTime(payout.processed_at)}</dd></div>
                <div><dt>Получатель</dt><dd>{payout.destination_masked || '—'}</dd></div>
                <div><dt>Причина отклонения</dt><dd>{payout.rejected_reason || '—'}</dd></div>
              </dl>
            </article>

            <article className="card stack">
              <h2>Ручные действия</h2>
              <div className={`notice ${payout.payout_eligibility?.is_eligible ? 'success' : 'warning'}`}>
                <strong>{payout.payout_eligibility?.is_eligible ? 'Юридически готов к выплате' : 'Выплату нельзя проводить'}</strong>
                <p className="muted">
                  KYC: {kycStatusText(payout.payout_eligibility?.kyc_status)} · договор: {payout.payout_eligibility?.has_active_agreement ? 'есть' : 'нет'} · профиль выплат: {payout.payout_eligibility?.has_verified_payout_profile ? 'заполнен' : 'не заполнен'}
                </p>
                {!payout.payout_eligibility?.is_eligible ? <p>{eligibilityReasonText(payout.payout_eligibility?.block_reason)}</p> : null}
              </div>
              <label className="field">
                External reference
                <input value={externalReference} onChange={(event) => setExternalReference(event.target.value)} placeholder="bank-batch-042" />
              </label>
              <label className="field">
                Отклонить reason
                <input value={rejectReason} onChange={(event) => setОтклонитьReason(event.target.value)} placeholder="Неверные реквизиты" />
              </label>
              <div className="inline wrap gap-sm">
                <button className="btn ghost" type="button" onClick={() => void transition('approve')} disabled={!!busy || !payout.payout_eligibility?.is_eligible || !(payout.status === 'pending' || payout.status === 'requested')}>Одобрить</button>
                <button className="btn ghost" type="button" onClick={() => void transition('processing')} disabled={!!busy || !payout.payout_eligibility?.is_eligible || payout.status !== 'approved'}>В обработку</button>
                <button className="btn" type="button" onClick={() => void transition('paid')} disabled={!!busy || !payout.payout_eligibility?.is_eligible || !(payout.status === 'processing' || payout.status === 'approved')}>Отметить оплаченной</button>
                <button className="btn danger" type="button" onClick={() => void transition('reject')} disabled={!!busy || payout.status === 'paid' || payout.status === 'rejected'}>Отклонить</button>
              </div>
            </article>
          </div>

          <article className="card stack">
            <h2>Записи ledger</h2>
            <LedgerTable entries={payout.ledger_entries ?? []} />
          </article>

          <article className="card stack">
            <h2>Сырые метаданные</h2>
            <pre>{prettyJson(payout.metadata)}</pre>
          </article>
        </>
      ) : null}
    </section>
  );
}
