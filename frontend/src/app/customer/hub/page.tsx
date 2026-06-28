'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { customerHubApi } from '@/lib/api';
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
  accessTypeLabel,
  formatCustomerMoney,
  orderStatusLabel,
  shortCustomerNumber,
  statusTone,
  subscriptionStatusLabel,
} from '@/modules/customer-cabinet/components/customer-format';
import type { CustomerMarketplaceHub } from '@/types/api';

function contentHref(type?: string, slug?: string) {
  if (!slug) return '/catalog';
  if (type === 'program') return `/catalog/programs/${slug}`;
  if (type === 'bundle') return `/catalog/bundles/${slug}`;
  return `/catalog/videos/${slug}`;
}

export default function CustomerHubPage() {
  const [days, setDays] = useState(30);
  const [hub, setHub] = useState<CustomerMarketplaceHub | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  async function load(selectedDays = days) {
    try {
      setLoading(true);
      setMessage('');
      setHub(await customerHubApi.getHub(selectedDays));
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Не удалось загрузить данные');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load(days);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days]);

  const currency = useMemo(() => hub?.orders.recent.find((order) => order.currency)?.currency || hub?.subscriptions.items[0]?.plan?.currency || 'RUB', [hub]);
  const metrics: CustomerMetric[] = [
    { label: 'Активные доступы', value: hub?.summary.active_entitlements_count ?? 0, hint: 'В библиотеке', tone: 'success' },
    { label: 'Покупки за период', value: formatCustomerMoney(hub?.summary.period_spent, currency), hint: `${days} дней`, tone: 'neutral' },
    { label: 'Оплаченные заказы', value: hub?.summary.paid_orders_count ?? 0, hint: 'Успешно', tone: 'success' },
    { label: 'Избранное', value: hub?.summary.favorites_count ?? 0, hint: 'Сохранено', tone: 'neutral' },
  ];

  return (
    <ProtectedPage title="Обзор" description="Покупательский кабинет доступен только авторизованным пользователям.">
      <CustomerCabinetShell
        title="Расширенный обзор"
        description="Готовность аккаунта, библиотека, покупки, подписки, рекомендации, избранное и отзывы."
        actions={
          <>
            <select className="select" value={days} onChange={(event) => setDays(Number(event.target.value))}>
              {[7, 30, 90].map((value) => <option key={value} value={value}>{value} дней</option>)}
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

        {hub ? (
          <div className="customer-dashboard-grid">
            <section className="customer-section-card">
              <div className="customer-section-header"><h2>Готовность аккаунта</h2></div>
              <div className="customer-commerce-list">
                {hub.readiness.checks.map((check) => (
                  <article className="customer-commerce-card" key={check.code}>
                    <CustomerStatusBadge tone={statusTone(check.status)}>{check.status === 'done' || check.status === 'ready' ? 'Готово' : 'Проверить'}</CustomerStatusBadge>
                    <strong>{check.title}</strong>
                  </article>
                ))}
              </div>
            </section>

            <section className="customer-section-card">
              <div className="customer-section-header"><h2>Библиотека</h2><Link href="/learning" className="premium-secondary-button">Перейти к обучению</Link></div>
              <div className="customer-commerce-list">
                {hub.library.items.slice(0, 8).map((item) => (
                  <Link className="customer-commerce-card" href={contentHref(item.target_type, item.slug)} key={item.id}>
                    <CustomerStatusBadge tone={statusTone(item.access_status || item.status)}>{item.access_status === 'active' ? 'Активен' : 'Доступ'}</CustomerStatusBadge>
                    <strong>{item.title || accessTypeLabel(item.target_type)}</strong>
                    <span>{item.trainer_name || 'TrainerHub'} · {accessTypeLabel(item.target_type)}</span>
                  </Link>
                ))}
                {!hub.library.items.length ? <CustomerEmptyState title="Библиотека пока пустая" description="После покупки материалы появятся здесь." /> : null}
              </div>
            </section>

            <section className="customer-section-card">
              <div className="customer-section-header"><h2>Недавние заказы</h2><Link href="/orders" className="premium-secondary-button">Все заказы</Link></div>
              <div className="customer-commerce-list">
                {hub.orders.recent.slice(0, 8).map((order) => (
                  <Link className="customer-commerce-card" href={`/orders/${order.id}`} key={order.id}>
                    <CustomerStatusBadge tone={statusTone(order.status)}>{orderStatusLabel(order.status)}</CustomerStatusBadge>
                    <strong>{order.items?.[0]?.title || 'Покупка TrainerHub'}</strong>
                    <span>{shortCustomerNumber(order.id, 'ORD')} · {formatCustomerMoney(order.total_amount, order.currency || currency)}</span>
                  </Link>
                ))}
                {!hub.orders.recent.length ? <CustomerEmptyState title="Заказов пока нет" description="История покупок появится здесь." /> : null}
              </div>
            </section>

            <section className="customer-section-card">
              <div className="customer-section-header"><h2>Подписки</h2><Link href="/subscriptions" className="premium-secondary-button">Управлять</Link></div>
              <div className="customer-commerce-list">
                {hub.subscriptions.items.slice(0, 6).map((item) => (
                  <article className="customer-commerce-card" key={item.id}>
                    <CustomerStatusBadge tone={statusTone(item.status)}>{subscriptionStatusLabel(item.status)}</CustomerStatusBadge>
                    <strong>{item.plan?.title || 'Подписка'}</strong>
                    <span>{item.plan?.period_days || 30} дней · {formatCustomerMoney(item.plan?.price, item.plan?.currency || currency)}</span>
                  </article>
                ))}
                {!hub.subscriptions.items.length ? <CustomerEmptyState title="Подписок пока нет" description="Подписки появятся после оформления." /> : null}
              </div>
            </section>

            <section className="customer-section-card">
              <div className="customer-section-header"><h2>Рекомендации</h2><Link href="/catalog" className="premium-secondary-button">Открыть каталог</Link></div>
              <div className="customer-commerce-list">
                {hub.recommendations.items.slice(0, 8).map((item) => (
                  <Link className="customer-commerce-card" href={contentHref(item.target_type, item.slug)} key={`${item.target_type}-${item.target_id}`}>
                    <strong>{item.title}</strong>
                    <span>{item.trainer_name || 'TrainerHub'} · {formatCustomerMoney(item.price_amount, item.currency || currency)}</span>
                  </Link>
                ))}
                {!hub.recommendations.items.length ? <CustomerEmptyState title="Рекомендаций пока нет" description="Новые материалы появятся после публикации тренерами." /> : null}
              </div>
            </section>

            <section className="customer-section-card">
              <div className="customer-section-header"><h2>Избранное</h2></div>
              <div className="customer-commerce-list">
                {hub.favorites.items.slice(0, 8).map((item) => (
                  <Link className="customer-commerce-card" href={item.target_type === 'trainer' ? `/trainers/${item.slug}` : contentHref(item.target_type, item.slug)} key={item.id}>
                    <strong>{item.title || 'Сохранённый материал'}</strong>
                    <span>{accessTypeLabel(item.target_type)}</span>
                  </Link>
                ))}
                {!hub.favorites.items.length ? <CustomerEmptyState title="Избранного пока нет" description="Сохраняйте тренеров и программы из каталога." /> : null}
              </div>
            </section>

            <section className="customer-section-card">
              <div className="customer-section-header"><h2>Отзывы</h2></div>
              <div className="customer-commerce-list">
                {hub.reviews.opportunities.slice(0, 6).map((item) => (
                  <Link className="customer-commerce-card" href={contentHref(item.target_type, item.slug)} key={`${item.target_type}-${item.target_id}`}>
                    <CustomerStatusBadge tone="warning">Оставить отзыв</CustomerStatusBadge>
                    <strong>{item.title || accessTypeLabel(item.target_type)}</strong>
                    <span>{item.trainer_name || 'тренер'}</span>
                  </Link>
                ))}
                {!hub.reviews.opportunities.length ? <CustomerEmptyState title="Новых отзывов нет" description="После завершения обучения здесь появятся материалы для отзыва." actionHref="/learning" actionLabel="Перейти к обучению" /> : null}
              </div>
            </section>
          </div>
        ) : null}
      </CustomerCabinetShell>
    </ProtectedPage>
  );
}
