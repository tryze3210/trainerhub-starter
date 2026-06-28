'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { privateApi } from '@/lib/api';
import {
  CustomerCabinetShell,
  CustomerEmptyState,
  CustomerErrorState,
  CustomerLoadingState,
  CustomerMetricCard,
  CustomerStatusBadge,
  type CustomerMetric,
} from '@/modules/customer-cabinet/components';
import {
  formatCustomerDate,
  formatCustomerMoney,
  orderAmount,
  orderStatusLabel,
  orderTitle,
  shortCustomerNumber,
  statusTone,
} from '@/modules/customer-cabinet/components/customer-format';
import type { Order } from '@/types/api';

export default function OrdersPage() {
  const [items, setItems] = useState<Order[]>([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const { isAuthenticated, isLoading: sessionLoading } = useAuthSession();

  async function load() {
    try {
      setLoading(true);
      setMessage('');
      setItems(await privateApi.listOrders());
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Не удалось загрузить данные');
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
    void load();
  }, [isAuthenticated, sessionLoading]);

  const stats = useMemo(() => {
    const paid = items.filter((item) => ['paid', 'completed'].includes((item.status || '').toLowerCase())).length;
    const pending = items.filter((item) => ['pending', 'awaiting_payment', 'created'].includes((item.status || '').toLowerCase())).length;
    const volume = items.reduce((sum, item) => sum + Number(item.total_amount || item.gross_amount || item.amount || 0), 0);
    return { paid, pending, volume };
  }, [items]);

  const metrics: CustomerMetric[] = [
    { label: 'Всего', value: items.length, hint: 'Все покупки', tone: 'neutral' },
    { label: 'Оплачено', value: stats.paid, hint: 'Доступы активируются', tone: 'success' },
    { label: 'Ожидают оплаты', value: stats.pending, hint: 'Можно завершить', tone: stats.pending ? 'warning' : 'neutral' },
    { label: 'Сумма покупок', value: formatCustomerMoney(stats.volume, 'RUB'), hint: 'За всё время', tone: 'neutral' },
  ];

  return (
    <ProtectedPage title="Мои заказы" description="Раздел заказов доступен только после авторизации.">
      <CustomerCabinetShell
        title="Мои заказы"
        description="История ваших покупок, статусы заказов и переход к деталям оплаты."
        actions={<button className="premium-secondary-button" type="button" onClick={() => void load()} disabled={loading}>Обновить</button>}
      >
        <div className="customer-metric-grid">
          {metrics.map((metric) => <CustomerMetricCard key={metric.label} metric={metric} />)}
        </div>
        {message ? <CustomerErrorState message={message} onRetry={() => void load()} /> : null}
        {loading ? <CustomerLoadingState /> : null}
        {!loading && !items.length ? <CustomerEmptyState title="Заказов пока нет" description="После оформления покупки заказ появится здесь." /> : null}

        <div className="customer-commerce-list">
          {items.map((item) => (
            <article className="customer-commerce-card" key={item.id}>
              <CustomerStatusBadge tone={statusTone(item.status)}>{orderStatusLabel(item.status)}</CustomerStatusBadge>
              <strong>{orderTitle(item)}</strong>
              <span>{shortCustomerNumber(item.id, 'ORD')} · {orderAmount(item)}</span>
              <div className="customer-commerce-list">
                <div><span>Создан</span><strong>{formatCustomerDate(item.created_at || item.createdAt)}</strong></div>
                <div><span>Оплачен</span><strong>{formatCustomerDate(item.paid_at || item.completed_at)}</strong></div>
              </div>
              <div className="customer-page-actions">
                <Link href={`/orders/${item.id}`} className="premium-secondary-button">Детали заказа</Link>
                <Link href="/payments" className="premium-secondary-button">Платёж</Link>
              </div>
            </article>
          ))}
        </div>
      </CustomerCabinetShell>
    </ProtectedPage>
  );
}
