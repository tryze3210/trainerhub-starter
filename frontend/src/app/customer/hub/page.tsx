'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { DSEmptyState, DSPageHeader, DSSection, DSSkeleton, DSStatsGrid, DSStatusDot, DSTransitionPanel } from '@/design-system';
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

function statusTone(status?: string): 'neutral' | 'primary' | 'success' | 'warning' | 'danger' {
  if (!status) return 'neutral';
  if (['active', 'available', 'paid', 'completed', 'ready', 'done'].includes(status)) return 'success';
  if (['failed', 'cancelled', 'revoked', 'expired', 'attention'].includes(status)) return 'danger';
  if (['pending', 'created', 'todo'].includes(status)) return 'warning';
  return 'neutral';
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
        <DSPageHeader
          eyebrow="Customer marketplace"
          title="Customer hub"
          description="Библиотека доступов, заказы, подписки, избранное, отзывы и рекомендации в одном customer-facing cockpit."
          actions={
            <>
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
            </>
          }
        />

        {loading ? <div className="card"><DSSkeleton lines={5} /></div> : null}
        {error ? <div className="card error">{error}</div> : null}

        {hub ? (
          <DSTransitionPanel active className="stack" style={{ gap: 24 }}>
            <DSStatsGrid
              stats={[
                { label: 'Активные доступы', value: hub.summary.active_entitlements_count, tone: 'success' },
                { label: 'Потрачено за период', value: formatMoney(hub.summary.period_spent, currency), tone: 'primary' },
                { label: 'Оплаченные заказы', value: hub.summary.paid_orders_count, tone: 'success' },
                { label: 'Избранное', value: hub.summary.favorites_count, tone: 'warning' },
              ]}
            />

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

              <DSSection title="Customer readiness" description="Готовность customer кабинета и access runtime.">
                <div className="card compact">
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {hub.readiness.checks.map((check) => (
                    <div className="list-item" key={check.code}>
                      <span>{check.title}</span>
                      <DSStatusDot tone={statusTone(check.status)} label={check.status} />
                    </div>
                  ))}
                </div>
                </div>
              </DSSection>
            </div>

            <div className="grid-2">
              <DSSection
                title="Моя библиотека"
                description="Активные доступы к видео, программам и bundles."
                actions={
                  <>
                    <Link className="button secondary" href="/learning">Обучение</Link>
                    <Link className="button secondary" href="/entitlements">Все доступы</Link>
                  </>
                }
              >
                <div className="card compact">
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {hub.library.items.length === 0 ? (
                    <DSEmptyState title="Нет купленного контента" description="Открой каталог и оформи первый доступ." />
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
              </DSSection>

              <DSSection title="Последние заказы" description="Недавние checkout/order операции." actions={<Link className="button secondary" href="/orders">Все заказы</Link>}>
                <div className="card compact">
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {hub.orders.recent.length === 0 ? (
                    <DSEmptyState title="Заказов пока нет" description="После checkout заказы появятся здесь." />
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
              </DSSection>
            </div>

            <div className="grid-2">
              <DSSection title="Подписки и платежи" description="Активные подписки и платежные проблемы." actions={<Link className="button secondary" href="/subscriptions">Подписки</Link>}>
                <div className="card compact">
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
                  {hub.subscriptions.items.length === 0 ? <DSEmptyState title="Активных подписок пока нет" description="Подписки появятся после покупки subscription продукта." /> : null}
                </div>
                </div>
              </DSSection>

              <DSSection title="Отзывы к написанию" description="Контент, по которому можно оставить feedback.">
                <div className="card compact">
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {hub.reviews.opportunities.length === 0 ? (
                    <DSEmptyState title="Нет новых позиций для отзыва" description="Новые review opportunities появятся после завершенного доступа." />
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
              </DSSection>
            </div>

            <div className="grid-2">
              <DSSection title="Избранное" description="Сохраненные тренеры, курсы и программы.">
                <div className="card compact">
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {hub.favorites.items.length === 0 ? (
                    <DSEmptyState title="Избранного пока нет" description="Сохраняй тренеров и программы из каталога." />
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
              </DSSection>

              <DSSection title="Рекомендации" description="Новые материалы из marketplace.">
                <div className="card compact">
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {hub.recommendations.items.length === 0 ? (
                    <DSEmptyState title="Рекомендаций пока нет" description="Рекомендации появятся после публикации контента тренерами." />
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
              </DSSection>
            </div>
          </DSTransitionPanel>
        ) : null}
      </section>
    </ProtectedPage>
  );
}
