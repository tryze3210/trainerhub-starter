'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { customerHubApi } from '@/lib/api';
import type { CustomerMarketplaceHub } from '@/types/api';

function formatMoney(value?: string | number, currency = 'RUB') {
  if (value === undefined || value === null || value === '') return `0.00 ${currency}`;
  return `${value} ${currency}`;
}

function statusBadge(status?: string) {
  if (!status) return 'badge secondary';
  if (['active', 'available', 'paid', 'completed', 'ready', 'done'].includes(status)) return 'badge success';
  if (['failed', 'cancelled', 'revoked', 'expired', 'attention'].includes(status)) return 'badge error';
  if (['pending', 'created', 'todo'].includes(status)) return 'badge warning';
  return 'badge secondary';
}

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
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        setLoading(true);
        setError('');
        const payload = await customerHubApi.getHub(days);
        if (!cancelled) setHub(payload);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Не удалось загрузить customer hub');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [days]);

  const currency = useMemo(() => {
    const paidOrder = hub?.orders.recent.find((order) => order.currency);
    return paidOrder?.currency || hub?.subscriptions.items[0]?.plan?.currency || 'RUB';
  }, [hub]);

  return (
    <ProtectedPage title="Customer hub" description="Покупательский marketplace-кабинет доступен только авторизованным пользователям.">
      <section className="stack" style={{ gap: 24 }}>
        <div className="row" style={{ justifyContent: 'space-between', gap: 16, alignItems: 'flex-start' }}>
          <div className="stack" style={{ gap: 10 }}>
            <span className="badge">Customer marketplace</span>
            <h1>Customer hub</h1>
            <p className="lead">Библиотека доступов, заказы, подписки, избранное, отзывы и рекомендации в одном customer-facing cockpit.</p>
          </div>
          <div className="row" style={{ gap: 8 }}>
            {[7, 30, 90].map((value) => (
              <button
                key={value}
                type="button"
                className={`button ${days === value ? 'primary' : 'secondary'}`}
                onClick={() => setDays(value)}
              >
                {value}d
              </button>
            ))}
          </div>
        </div>

        {loading ? <div className="card"><p className="muted">Загружаем customer hub…</p></div> : null}
        {error ? <div className="card error">{error}</div> : null}

        {hub ? (
          <>
            <div className="grid-4">
              <div className="card"><div className="kpi"><span className="muted">Активные доступы</span><strong>{hub.summary.active_entitlements_count}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Потрачено за период</span><strong>{formatMoney(hub.summary.period_spent, currency)}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Оплаченные заказы</span><strong>{hub.summary.paid_orders_count}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Избранное</span><strong>{hub.summary.favorites_count}</strong></div></div>
            </div>

            <div className="grid-2">
              <div className="card dark hero">
                <div className="stack" style={{ gap: 12 }}>
                  <span className={statusBadge(hub.readiness.status)}>{hub.readiness.status}</span>
                  <h2 className="title-lg" style={{ margin: 0 }}>{hub.profile.display_name || hub.profile.email || 'Customer'}</h2>
                  <p>Streak: {hub.profile.streak_count || 0} · Активные подписки: {hub.summary.active_subscriptions_count}</p>
                  <div className="inline">
                    <Link className="button" href="/catalog">Открыть каталог</Link>
                    <Link className="button secondary" href="/orders">История заказов</Link>
                  </div>
                </div>
              </div>

              <div className="card">
                <h2 className="title-md">Customer readiness</h2>
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {hub.readiness.checks.map((check) => (
                    <div className="list-item" key={check.code}>
                      <span>{check.title}</span>
                      <span className={statusBadge(check.status)}>{check.status}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="grid-2">
              <div className="card">
                <div className="row" style={{ justifyContent: 'space-between', gap: 12 }}>
                  <h2 className="title-md" style={{ margin: 0 }}>Моя библиотека</h2>
                  <Link className="button secondary" href="/entitlements">Все доступы</Link>
                </div>
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {hub.library.items.length === 0 ? (
                    <p className="muted">Пока нет купленного контента. Открой каталог и оформи первый доступ.</p>
                  ) : (
                    hub.library.items.slice(0, 8).map((item) => (
                      <Link className="list-item" href={contentHref(item.target_type, item.slug)} key={item.id}>
                        <div className="stack" style={{ gap: 2 }}>
                          <strong>{item.title || item.target_type}</strong>
                          <small>{item.trainer_name || 'trainer'} · {item.target_type}</small>
                        </div>
                        <span className={statusBadge(item.access_status || item.status)}>{item.access_status || item.status}</span>
                      </Link>
                    ))
                  )}
                </div>
              </div>

              <div className="card">
                <div className="row" style={{ justifyContent: 'space-between', gap: 12 }}>
                  <h2 className="title-md" style={{ margin: 0 }}>Последние заказы</h2>
                  <Link className="button secondary" href="/orders">Все заказы</Link>
                </div>
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {hub.orders.recent.length === 0 ? (
                    <p className="muted">Заказов пока нет.</p>
                  ) : (
                    hub.orders.recent.slice(0, 8).map((order) => (
                      <Link className="list-item" href={`/orders/${order.id}`} key={order.id}>
                        <div className="stack" style={{ gap: 2 }}>
                          <strong>{formatMoney(order.total_amount, order.currency || currency)}</strong>
                          <small>{order.items?.[0]?.title || order.order_type || 'order'}</small>
                        </div>
                        <span className={statusBadge(order.status)}>{order.status}</span>
                      </Link>
                    ))
                  )}
                </div>
              </div>
            </div>

            <div className="grid-2">
              <div className="card">
                <div className="row" style={{ justifyContent: 'space-between', gap: 12 }}>
                  <h2 className="title-md" style={{ margin: 0 }}>Подписки и платежи</h2>
                  <Link className="button secondary" href="/subscriptions">Подписки</Link>
                </div>
                <div className="grid-2" style={{ marginTop: 16 }}>
                  <div className="card compact"><div className="kpi"><span className="muted">Активные подписки</span><strong>{hub.subscriptions.summary.active_count}</strong></div></div>
                  <div className="card compact"><div className="kpi"><span className="muted">Проблемные платежи</span><strong>{hub.payments.summary.failed_count}</strong></div></div>
                </div>
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {hub.subscriptions.items.slice(0, 4).map((subscription) => (
                    <div className="list-item" key={subscription.id}>
                      <div className="stack" style={{ gap: 2 }}>
                        <strong>{subscription.plan?.title || 'Subscription'}</strong>
                        <small>{subscription.plan?.period_days || 30} days · {formatMoney(subscription.plan?.price, subscription.plan?.currency || currency)}</small>
                      </div>
                      <span className={statusBadge(subscription.status)}>{subscription.status}</span>
                    </div>
                  ))}
                  {hub.subscriptions.items.length === 0 ? <p className="muted">Активных подписок пока нет.</p> : null}
                </div>
              </div>

              <div className="card">
                <h2 className="title-md">Отзывы к написанию</h2>
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {hub.reviews.opportunities.length === 0 ? (
                    <p className="muted">Нет новых позиций для отзыва.</p>
                  ) : (
                    hub.reviews.opportunities.slice(0, 6).map((item) => (
                      <Link className="list-item" href={contentHref(item.target_type, item.slug)} key={`${item.target_type}-${item.target_id}`}>
                        <div className="stack" style={{ gap: 2 }}>
                          <strong>{item.title || item.target_type}</strong>
                          <small>{item.trainer_name || 'trainer'}</small>
                        </div>
                        <span className="badge warning">review</span>
                      </Link>
                    ))
                  )}
                </div>
              </div>
            </div>

            <div className="grid-2">
              <div className="card">
                <h2 className="title-md">Избранное</h2>
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {hub.favorites.items.length === 0 ? (
                    <p className="muted">Пока нет избранных тренеров или программ.</p>
                  ) : (
                    hub.favorites.items.slice(0, 8).map((item) => (
                      <Link className="list-item" href={item.target_type === 'trainer' ? `/trainers/${item.slug}` : contentHref(item.target_type, item.slug)} key={item.id}>
                        <span>{item.title || item.target_id}</span>
                        <span className="badge secondary">{item.target_type}</span>
                      </Link>
                    ))
                  )}
                </div>
              </div>

              <div className="card">
                <h2 className="title-md">Рекомендации</h2>
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {hub.recommendations.items.length === 0 ? (
                    <p className="muted">Рекомендации появятся после публикации контента тренерами.</p>
                  ) : (
                    hub.recommendations.items.slice(0, 8).map((item) => (
                      <Link className="list-item" href={contentHref(item.target_type, item.slug)} key={`${item.target_type}-${item.target_id}`}>
                        <div className="stack" style={{ gap: 2 }}>
                          <strong>{item.title}</strong>
                          <small>{item.trainer_name || 'trainer'} · {item.difficulty || 'any level'}</small>
                        </div>
                        <strong>{formatMoney(item.price_amount, item.currency || currency)}</strong>
                      </Link>
                    ))
                  )}
                </div>
              </div>
            </div>
          </>
        ) : null}
      </section>
    </ProtectedPage>
  );
}
