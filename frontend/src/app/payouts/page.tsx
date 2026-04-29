'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { privateApi } from '@/lib/api';
import type { PayoutBalance, PayoutRequest } from '@/types/api';

function formatMoney(value?: string | number, currency = 'RUB'): string {
  if (value === undefined || value === null || value === '') return `— ${currency}`;
  return `${value} ${currency}`;
}

function formatDate(value?: string | null): string {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

export default function PayoutsPage() {
  const { user } = useAuthSession();
  const isTrainer = user?.active_role === 'trainer';
  const [balance, setBalance] = useState<PayoutBalance | null>(null);
  const [items, setItems] = useState<PayoutRequest[]>([]);
  const [msg, setMsg] = useState('');
  const [busy, setBusy] = useState(false);
  const [amount, setAmount] = useState('0');
  const [destination, setDestination] = useState('**** 4242');

  async function load() {
    try {
      setMsg('');
      const [balancePayload, listPayload] = await Promise.all([
        privateApi.getPayoutBalance(),
        privateApi.listPayouts(),
      ]);
      setBalance(balancePayload);
      setItems(listPayload);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить payout ledger');
    }
  }

  useEffect(() => {
    if (!isTrainer) return;
    void load();
  }, [isTrainer]);

  const stats = useMemo(() => ({
    requested: items.length,
    paid: items.filter((item) => item.status === 'paid').length,
    pending: items.filter((item) => item.status === 'pending' || item.status === 'approved' || item.status === 'processing').length,
  }), [items]);

  async function onRequest() {
    try {
      setBusy(true);
      setMsg('');
      await privateApi.requestPayout({ amount, destination_masked: destination });
      setAmount('0');
      await load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось создать payout request');
    } finally {
      setBusy(false);
    }
  }

  return (
    <ProtectedPage title="Payouts" description="Раздел payout доступен только тренерам.">
      {!isTrainer ? (
        <div className="card error">Текущая сессия не имеет trainer-role.</div>
      ) : (
        <section className="stack" style={{ gap: 24 }}>
          <div className="row" style={{ alignItems: 'flex-start' }}>
            <div className="stack" style={{ gap: 10 }}>
              <span className="badge secondary">Trainer finance</span>
              <h1>Payouts</h1>
              <p className="lead">Баланс тренера, запросы на вывод и detail pages по каждому payout request.</p>
            </div>
            <button className="button secondary" onClick={() => void load()}>Обновить</button>
          </div>

          {msg ? <div className="card error">{msg}</div> : null}

          <div className="grid-4">
            <div className="card"><div className="kpi"><span className="muted">Available</span><strong>{formatMoney(balance?.available_amount, balance?.currency || 'RUB')}</strong></div></div>
            <div className="card"><div className="kpi"><span className="muted">Reserved</span><strong>{formatMoney(balance?.reserved_amount, balance?.currency || 'RUB')}</strong></div></div>
            <div className="card"><div className="kpi"><span className="muted">Lifetime earned</span><strong>{formatMoney(balance?.lifetime_earned_amount, balance?.currency || 'RUB')}</strong></div></div>
            <div className="card"><div className="kpi"><span className="muted">Requests</span><strong>{stats.requested}</strong></div></div>
          </div>

          <div className="grid-2">
            <div className="card">
              <h3>Новый payout request</h3>
              <div className="form" style={{ marginTop: 16 }}>
                <div className="form-group">
                  <label className="label" htmlFor="payout-amount">Сумма</label>
                  <input id="payout-amount" className="input" value={amount} onChange={(event) => setAmount(event.target.value)} placeholder="1500.00" />
                </div>
                <div className="form-group">
                  <label className="label" htmlFor="payout-destination">Реквизиты (masked)</label>
                  <input id="payout-destination" className="input" value={destination} onChange={(event) => setDestination(event.target.value)} placeholder="**** 4242" />
                </div>
                <button className="button" disabled={busy} onClick={() => void onRequest()}>
                  {busy ? 'Создаём...' : 'Запросить вывод'}
                </button>
              </div>
            </div>
            <div className="card">
              <h3>Сводка</h3>
              <div className="stack" style={{ gap: 12, marginTop: 16 }}>
                <div className="list-item"><span className="muted">Pending / approved / processing</span><strong>{stats.pending}</strong></div>
                <div className="list-item"><span className="muted">Paid</span><strong>{stats.paid}</strong></div>
                <div className="list-item"><span className="muted">Последнее обновление баланса</span><strong>{formatDate(balance?.updated_at)}</strong></div>
              </div>
            </div>
          </div>

          {items.length === 0 ? (
            <div className="empty-state"><h3>Payout requests пока нет</h3><p>После успешных продаж и accrual появится доступный баланс.</p></div>
          ) : (
            <div className="grid-2">
              {items.map((item) => (
                <article className="card" key={item.id}>
                  <div className="stack" style={{ gap: 12 }}>
                    <div className="row">
                      <strong>{formatMoney(item.amount, item.currency || 'RUB')}</strong>
                      <span className="badge secondary">{item.status || '—'}</span>
                    </div>
                    <div className="grid-2">
                      <div className="list-item"><span className="muted">Реквизиты</span><strong>{item.destination_masked || '—'}</strong></div>
                      <div className="list-item"><span className="muted">Запрошен</span><strong>{formatDate(item.requested_at || item.created_at)}</strong></div>
                    </div>
                    <div className="inline">
                      <Link href={`/payouts/${item.id}`} className="button secondary">Детали</Link>
                      <Link href="/payments" className="button ghost">Платежи</Link>
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
