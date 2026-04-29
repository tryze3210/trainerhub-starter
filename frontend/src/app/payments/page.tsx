'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { privateApi } from '@/lib/api';
import type { Payment } from '@/types/api';

function formatMoney(value?: string | number, currency = 'RUB'): string {
  if (value === undefined || value === null || value === '') return `— ${currency}`;
  return `${value} ${currency}`;
}

function formatDate(value?: string | null): string {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

export default function PaymentsPage() {
  const [list, setList] = useState<Payment[]>([]);
  const [msg, setMsg] = useState('');
  const [loading, setLoading] = useState(true);
  const { isAuthenticated, isLoading: sessionLoading, user } = useAuthSession();
  const isTrainer = user?.active_role === 'trainer';

  async function loadPayments() {
    try {
      setLoading(true);
      setMsg('');
      setList(await privateApi.listPayments());
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить платежи');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (sessionLoading) return;
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }
    void loadPayments();
  }, [isAuthenticated, sessionLoading]);

  const stats = useMemo(() => ({
    total: list.length,
    paid: list.filter((item) => (item.status || '').toLowerCase() === 'succeeded').length,
    pending: list.filter((item) => (item.status || '').toLowerCase() === 'pending').length,
    volume: list.reduce((acc, item) => acc + Number(item.amount || 0), 0),
  }), [list]);

  return (
    <ProtectedPage title="Платежи" description="История платежей доступна только авторизованным пользователям.">
      <section className="stack" style={{ gap: 28 }}>
        <div className="row" style={{ alignItems: 'flex-start' }}>
          <div className="stack" style={{ gap: 10 }}>
            <span className="badge secondary">Payments</span>
            <h1>Платежи</h1>
            <p className="lead">Payment ledger с детальными страницами, mock confirm/cancel и provider-specific checkout contract.</p>
          </div>
          <div className="inline">
            <button className="button secondary" onClick={() => void loadPayments()}>Обновить</button>
            <Link href="/orders" className="button ghost">Заказы</Link>
            {isTrainer ? <Link href="/payouts" className="button ghost">Payouts</Link> : null}
          </div>
        </div>

        <div className="grid-4">
          <div className="card"><div className="kpi"><span className="muted">Всего платежей</span><strong>{stats.total}</strong></div></div>
          <div className="card"><div className="kpi"><span className="muted">Успешные</span><strong>{stats.paid}</strong></div></div>
          <div className="card"><div className="kpi"><span className="muted">В ожидании</span><strong>{stats.pending}</strong></div></div>
          <div className="card"><div className="kpi"><span className="muted">Оборот</span><strong>{stats.volume.toFixed(2)} RUB</strong></div></div>
        </div>

        {msg ? <div className="card error">{msg}</div> : null}
        {loading ? (
          <div className="card">Загрузка платежей...</div>
        ) : list.length === 0 ? (
          <div className="empty-state"><h3>Платежей пока нет</h3><p>После checkout они появятся в этом разделе.</p></div>
        ) : (
          <div className="grid-2">
            {list.map((item) => (
              <article className="card" key={item.id}>
                <div className="stack" style={{ gap: 14 }}>
                  <div className="row">
                    <strong>{item.id}</strong>
                    <span className="badge secondary">{item.status || '—'}</span>
                  </div>
                  <div className="grid-2">
                    <div className="list-item"><span className="muted">Провайдер</span><strong>{item.provider || '—'}</strong></div>
                    <div className="list-item"><span className="muted">Сумма</span><strong>{formatMoney(item.amount, item.currency || 'RUB')}</strong></div>
                    <div className="list-item"><span className="muted">Создан</span><strong>{formatDate(item.created_at)}</strong></div>
                    <div className="list-item"><span className="muted">Подтверждён</span><strong>{formatDate(item.confirmed_at)}</strong></div>
                  </div>
                  <div className="inline">
                    <Link href={`/payments/${item.id}`} className="button secondary">Детали платежа</Link>
                    {item.order_id ? <Link href={`/orders/${item.order_id}`} className="button ghost">Заказ</Link> : null}
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </ProtectedPage>
  );
}
