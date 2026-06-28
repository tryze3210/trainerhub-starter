'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import {
  subscriptionsApi,
  type SubscriptionCenter,
  type SubscriptionItem,
} from '@/modules/subscriptions/api';
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
  statusTone,
  subscriptionStatusLabel,
  subscriptionTitle,
} from '@/modules/customer-cabinet/components/customer-format';

const dayOptions = [7, 30, 90, 180];

function isActive(item: SubscriptionItem) {
  return ['trial', 'active'].includes((item.status || '').toLowerCase()) || Boolean(item.is_active);
}

function isPending(item: SubscriptionItem) {
  return ['pending', 'past_due'].includes((item.status || '').toLowerCase());
}

export default function SubscriptionsPage() {
  const [days, setDays] = useState(30);
  const [center, setCenter] = useState<SubscriptionCenter | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  async function load(selectedDays = days) {
    try {
      setLoading(true);
      setMessage('');
      setCenter(await subscriptionsApi.getCenter(selectedDays));
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Не удалось загрузить данные');
    } finally {
      setLoading(false);
    }
  }

  async function cancelSubscription(id: string) {
    try {
      setMessage('');
      await subscriptionsApi.cancel(id, 'customer_cancel');
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Не удалось отменить подписку');
    }
  }

  async function resumeSubscription(id: string) {
    try {
      setMessage('');
      await subscriptionsApi.resume(id, 'customer_resume');
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Не удалось возобновить подписку');
    }
  }

  async function refreshAccesses(id: string) {
    try {
      setMessage('');
      await subscriptionsApi.syncEntitlements(id, 'customer_refresh_accesses');
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Не удалось обновить доступы');
    }
  }

  useEffect(() => {
    void load(days);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days]);

  const items = useMemo(() => center?.items || [], [center]);
  const active = useMemo(() => items.filter(isActive), [items]);
  const pending = useMemo(() => items.filter(isPending), [items]);
  const history = useMemo(() => items.filter((item) => !isActive(item) && !isPending(item)), [items]);
  const metrics: CustomerMetric[] = [
    { label: 'Всего', value: center?.summary.total_count ?? items.length, hint: 'Все подписки', tone: 'neutral' },
    { label: 'Активные', value: active.length, hint: 'Доступ открыт', tone: 'success' },
    { label: 'Ожидают оплаты', value: pending.length, hint: 'Требуется действие', tone: pending.length ? 'warning' : 'neutral' },
    { label: 'Автопродление', value: center?.summary.auto_renew_count ?? 0, hint: 'Включено', tone: 'neutral' },
  ];

  function renderSubscription(item: SubscriptionItem) {
    return (
      <article key={item.id} className="customer-commerce-card">
        <CustomerStatusBadge tone={statusTone(item.status, item.is_active)}>{subscriptionStatusLabel(item.status)}</CustomerStatusBadge>
        <strong>{subscriptionTitle(item)}</strong>
        <span>{formatCustomerMoney(item.amount || item.plan?.price, item.currency || item.plan?.currency || 'RUB')}</span>
        <div className="customer-commerce-list">
          <div><span>Начало</span><strong>{formatCustomerDate(item.starts_at || item.started_at || item.current_period_start)}</strong></div>
          <div><span>Период до</span><strong>{formatCustomerDate(item.ends_at || item.current_period_end)}</strong></div>
          <div><span>Доступы</span><strong>{item.entitlement_count ?? 0}</strong></div>
          <div><span>Продление</span><strong>{item.auto_renew ? 'Включено' : 'Выключено'}</strong></div>
        </div>
        <div className="customer-page-actions">
          {(item.lifecycle?.can_cancel || item.status === 'active') ? (
            <button className="premium-secondary-button" type="button" onClick={() => void cancelSubscription(item.id)}>Отменить подписку</button>
          ) : null}
          {(item.lifecycle?.can_resume || item.status === 'cancelled') ? (
            <button className="premium-primary-button" type="button" onClick={() => void resumeSubscription(item.id)}>Возобновить подписку</button>
          ) : null}
          <button className="premium-secondary-button" type="button" onClick={() => void refreshAccesses(item.id)}>Обновить доступы</button>
        </div>
      </article>
    );
  }

  return (
    <ProtectedPage title="Мои подписки" description="Подписки доступны только авторизованным пользователям.">
      <CustomerCabinetShell
        title="Мои подписки"
        description="Управляйте активными подписками, продлением и доступами к материалам."
        actions={
          <>
            <select className="select" value={days} onChange={(event) => setDays(Number(event.target.value))}>
              {dayOptions.map((option) => <option key={option} value={option}>{option} дней</option>)}
            </select>
            <button className="premium-secondary-button" type="button" onClick={() => void load()} disabled={loading}>Обновить</button>
          </>
        }
      >
        <div className="customer-metric-grid">
          {metrics.map((metric) => <CustomerMetricCard key={metric.label} metric={metric} />)}
        </div>
        {message ? <CustomerErrorState message={message} onRetry={() => void load()} /> : null}
        {loading ? <CustomerLoadingState /> : null}

        <section className="customer-section-card">
          <div className="customer-section-header"><h2>Активные подписки</h2></div>
          <div className="customer-commerce-list">
            {active.map(renderSubscription)}
            {!active.length && !loading ? <CustomerEmptyState title="Активных подписок пока нет" description="Подписки появятся после покупки." /> : null}
          </div>
        </section>

        <section className="customer-section-card">
          <div className="customer-section-header"><h2>Ожидают оплаты</h2></div>
          <div className="customer-commerce-list">
            {pending.map(renderSubscription)}
            {!pending.length && !loading ? <CustomerEmptyState title="Нет подписок, ожидающих оплаты" description="Все подписки сейчас без срочных действий." actionHref="/subscriptions" actionLabel="Остаться здесь" /> : null}
          </div>
        </section>

        <section className="customer-section-card">
          <div className="customer-section-header">
            <h2>История подписок</h2>
            <Link href="/entitlements" className="premium-secondary-button">Доступы по подпискам</Link>
          </div>
          <div className="customer-commerce-list">
            {history.map(renderSubscription)}
            {!history.length && !loading ? <CustomerEmptyState title="История пока пустая" description="Завершённые подписки появятся здесь." actionHref="/catalog" actionLabel="Открыть каталог" /> : null}
          </div>
        </section>
      </CustomerCabinetShell>
    </ProtectedPage>
  );
}
