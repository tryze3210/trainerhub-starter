'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { privateApi } from '@/lib/api';
import type { Order } from '@/types/api';

function formatDate(value?: string | null): string {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function formatMoney(order: Order): string {
  const value = order.total_amount ?? order.gross_amount ?? order.amount ?? '—';
  return `${value} ${order.currency || 'RUB'}`;
}

export default function OrdersPage() {
  const [list, setList] = useState<Order[]>([]);
  const [msg, setMsg] = useState('');
  const [loading, setLoading] = useState(true);
  const { isAuthenticated, isLoading: sessionLoading } = useAuthSession();

  async function loadOrders() {
    try {
      setLoading(true);
      setMsg('');
      setList(await privateApi.listOrders());
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить заказы');
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
    void loadOrders();
  }, [isAuthenticated, sessionLoading]);

  const stats = useMemo(() => {
    const totalVolume = list.reduce((acc, item) => acc + Number(item.total_amount || 0), 0);
    return {
      total: list.length,
      paid: list.filter((item) => ['paid', 'completed'].includes((item.status || '').toLowerCase())).length,
      pending: list.filter((item) => ['pending', 'awaiting_payment'].includes((item.status || '').toLowerCase())).length,
      totalVolume,
    };
  }, [list]);

  return (
    <ProtectedPage title="Заказы" description="Раздел заказов доступен только после авторизации.">
      <section className="stack" style={{ gap: 28 }}>
        <div className="row" style={{ alignItems: 'flex-start' }}>
          <div className="stack" style={{ gap: 10 }}>
            <span className="badge">Orders</span>
            <h1>Заказы</h1>
            <p className="lead">История заказов с переходом в detail page каждого order и связанного payment flow.</p>
          </div>
          <div className="inline">
            <button className="button secondary" onClick={() => void loadOrders()}>Обновить</button>
            <Link href="/cabinet" className="button ghost">Кабинет</Link>
          </div>
        </div>

        <div className="grid-4">
          <div className="card"><div className="kpi"><span className="muted">Всего заказов</span><strong>{stats.total}</strong></div></div>
          <div className="card"><div className="kpi"><span className="muted">Оплачено</span><strong>{stats.paid}</strong></div></div>
          <div className="card"><div className="kpi"><span className="muted">В ожидании</span><strong>{stats.pending}</strong></div></div>
          <div className="card"><div className="kpi"><span className="muted">Сумма заказов</span><strong>{stats.totalVolume.toFixed(2)} RUB</strong></div></div>
        </div>

        {msg ? <div className="card error">{msg}</div> : null}
        {loading ? (
          <div className="card">Загрузка заказов...</div>
        ) : list.length === 0 ? (
          <div className="empty-state"><h3>Заказов пока нет</h3><p>После checkout они появятся здесь.</p></div>
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
                    <div className="list-item"><span className="muted">Тип</span><strong>{item.order_type || '—'}</strong></div>
                    <div className="list-item"><span className="muted">Сумма</span><strong>{formatMoney(item)}</strong></div>
                    <div className="list-item"><span className="muted">Создан</span><strong>{formatDate(item.created_at || item.createdAt)}</strong></div>
                    <div className="list-item"><span className="muted">Оплачен</span><strong>{formatDate(item.paid_at)}</strong></div>
                  </div>
                  <div className="inline">
                    <Link href={`/orders/${item.id}`} className="button secondary">Детали заказа</Link>
                    <Link href="/payments" className="button ghost">Платежи</Link>
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
