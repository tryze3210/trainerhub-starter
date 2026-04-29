'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { privateApi } from '@/lib/api';
import type { Order } from '@/types/api';

function formatDate(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

export default function OrderDetailPage() {
  const params = useParams<{ id: string }>();
  const [order, setOrder] = useState<Order | null>(null);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    if (!params?.id) return;
    void (async () => {
      try {
        setMsg('');
        const data = await privateApi.getOrder(params.id);
        setOrder(data);
      } catch (err) {
        setMsg(err instanceof Error ? err.message : 'Не удалось загрузить заказ');
      }
    })();
  }, [params?.id]);

  return (
    <ProtectedPage title="Детали заказа" description="Страница заказа доступна только после входа.">
      {msg ? <div className="card error">{msg}</div> : null}
      {!order ? (
        <div className="card">Загрузка заказа...</div>
      ) : (
        <section className="stack" style={{ gap: 24 }}>
          <div className="card dark">
            <span className="badge">Order detail</span>
            <h1 className="title-lg">Заказ #{order.id}</h1>
            <p className="lead">Статус: {order.status || '—'} · Сумма: {order.total_amount || '—'} {order.currency || 'RUB'}</p>
          </div>
          <div className="grid-2">
            <div className="card">
              <h3>Основное</h3>
              <div className="stack" style={{ gap: 8, marginTop: 14 }}>
                <div><strong>Тип:</strong> {order.order_type || '—'}</div>
                <div><strong>Создан:</strong> {formatDate(order.created_at)}</div>
                <div><strong>Оплачен:</strong> {formatDate(order.paid_at)}</div>
                <div><strong>Завершён:</strong> {formatDate(order.completed_at)}</div>
              </div>
            </div>
            <div className="card">
              <h3>Позиции</h3>
              <div className="stack" style={{ gap: 10, marginTop: 14 }}>
                {order.items?.map((item) => (
                  <div className="card compact" key={item.id}>
                    <strong>{item.title_snapshot || item.item_type}</strong>
                    <p className="muted">{item.item_type} · qty {item.quantity || 1} · {item.total_price || item.unit_price || '—'} {order.currency || 'RUB'}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="inline">
            <Link href="/orders" className="button secondary">Назад к заказам</Link>
            <Link href="/payments" className="button ghost">Платежи</Link>
          </div>
        </section>
      )}
    </ProtectedPage>
  );
}
