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
  paymentStatusLabel,
  paymentTitle,
  shortCustomerNumber,
  statusTone,
} from '@/modules/customer-cabinet/components/customer-format';
import type { Payment } from '@/types/api';

export default function PaymentsPage() {
  const [items, setItems] = useState<Payment[]>([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const { isAuthenticated, isLoading: sessionLoading } = useAuthSession();

  async function load() {
    try {
      setLoading(true);
      setMessage('');
      setItems(await privateApi.listPayments());
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

  const stats = useMemo(() => ({
    success: items.filter((item) => ['succeeded', 'paid', 'completed'].includes((item.status || '').toLowerCase())).length,
    pending: items.filter((item) => ['pending', 'created'].includes((item.status || '').toLowerCase())).length,
    failed: items.filter((item) => ['failed', 'cancelled', 'canceled'].includes((item.status || '').toLowerCase())).length,
    volume: items.reduce((sum, item) => sum + Number(item.amount || item.gross_amount || 0), 0),
  }), [items]);

  const metrics: CustomerMetric[] = [
    { label: 'Успешные', value: stats.success, hint: 'Подтверждены', tone: 'success' },
    { label: 'В ожидании', value: stats.pending, hint: 'Обрабатываются', tone: stats.pending ? 'warning' : 'neutral' },
    { label: 'Не прошли', value: stats.failed, hint: 'Нужна проверка', tone: stats.failed ? 'danger' : 'neutral' },
    { label: 'Оборот', value: formatCustomerMoney(stats.volume, 'RUB'), hint: 'По платежам', tone: 'neutral' },
  ];

  return (
    <ProtectedPage title="Платежи" description="История платежей доступна только авторизованным пользователям.">
      <CustomerCabinetShell
        title="Платежи"
        description="Статусы оплат, подтверждения и история платёжных операций."
        actions={<button className="premium-secondary-button" type="button" onClick={() => void load()} disabled={loading}>Обновить</button>}
      >
        <div className="customer-metric-grid">
          {metrics.map((metric) => <CustomerMetricCard key={metric.label} metric={metric} />)}
        </div>
        {message ? <CustomerErrorState message={message} onRetry={() => void load()} /> : null}
        {loading ? <CustomerLoadingState /> : null}
        {!loading && !items.length ? <CustomerEmptyState title="Платежей пока нет" description="После оплаты история появится здесь." /> : null}

        <div className="customer-commerce-list">
          {items.map((item) => (
            <article className="customer-commerce-card" key={item.id}>
              <CustomerStatusBadge tone={statusTone(item.status)}>{paymentStatusLabel(item.status)}</CustomerStatusBadge>
              <strong>{paymentTitle(item)}</strong>
              <span>{shortCustomerNumber(item.id, 'PAY')} · {formatCustomerMoney(item.amount || item.gross_amount, item.currency || 'RUB')}</span>
              <div className="customer-commerce-list">
                <div><span>Платёжный провайдер</span><strong>{item.provider || 'TrainerHub'}</strong></div>
                <div><span>Создан</span><strong>{formatCustomerDate(item.created_at)}</strong></div>
                <div><span>Подтверждён</span><strong>{formatCustomerDate(item.confirmed_at)}</strong></div>
              </div>
              <div className="customer-page-actions">
                <Link href={`/payments/${item.id}`} className="premium-secondary-button">Детали платежа</Link>
                {item.order_id ? <Link href={`/orders/${item.order_id}`} className="premium-secondary-button">Заказ</Link> : null}
              </div>
            </article>
          ))}
        </div>
      </CustomerCabinetShell>
    </ProtectedPage>
  );
}
