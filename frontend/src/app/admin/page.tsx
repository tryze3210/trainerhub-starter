'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { isAdminUser } from '@/lib/authz';
import { privateApi } from '@/lib/api';
import type { AdminPayoutOverview, AnalyticsKpiOverview, ModerationOverview, Review } from '@/types/api';

type AdminCockpitState = {
  analytics: AnalyticsKpiOverview | null;
  payouts: AdminPayoutOverview | null;
  moderation: ModerationOverview | null;
  reviews: Review[];
};

function money(value?: string | number, currency = 'RUB') {
  if (value === undefined || value === null || value === '') return `0 ${currency}`;
  return `${value} ${currency}`;
}

function moderationOpenTotal(moderation?: ModerationOverview | null) {
  return (moderation?.totals.open || 0) + (moderation?.totals.in_review || 0) + (moderation?.totals.escalated || 0);
}

function statusDotClass(tone: 'success' | 'warning' | 'danger' = 'success') {
  if (tone === 'danger') return 'admin-status-dot admin-status-dot--danger';
  if (tone === 'warning') return 'admin-status-dot admin-status-dot--warning';
  return 'admin-status-dot';
}

function barFillClass(value: number, max: number) {
  const percent = Math.max(10, Math.ceil((value / Math.max(max, 1)) * 10) * 10);
  return `admin-bar-fill admin-bar-fill--${Math.min(percent, 100)}`;
}

export default function AdminCockpitPage() {
  const { user } = useAuthSession();
  const isAdmin = isAdminUser(user);
  const [state, setState] = useState<AdminCockpitState | null>(null);
  const [msg, setMsg] = useState('');

  async function load() {
    try {
      setMsg('');
      const [analytics, payouts, moderation, reviewsPayload] = await Promise.all([
        privateApi.getAdminAnalyticsOverview(30).catch(() => null),
        privateApi.getAdminPayoutOverview().catch(() => null),
        privateApi.getAdminModerationOverview().catch(() => null),
        privateApi.listPendingReviews().catch(() => ({ results: [] })),
      ]);

      setState({
        analytics,
        payouts,
        moderation,
        reviews: reviewsPayload.results || [],
      });
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить админ-панель');
    }
  }

  useEffect(() => {
    if (!isAdmin) return;
    void load();
  }, [isAdmin]);

  const openModeration = moderationOpenTotal(state?.moderation);
  const maxPayoutBucket = Math.max(...(state?.payouts?.statuses || []).map((bucket) => bucket.count), 1);

  return (
    <ProtectedPage title="Админ-панель" description="Операционный центр TrainerHub.">
      {!isAdmin ? (
        <section className="admin-alert">
          <h3>Нет доступа к админ-панели</h3>
          <p>У текущей сессии нет прав администратора. Войдите под суперпользователем или аккаунтом сотрудника.</p>
        </section>
      ) : (
        <section className="admin-cockpit">
          <section className="admin-hero">
            <div className="admin-hero__copy">
              <span className="admin-eyebrow">Операционный центр</span>
              <h2>Панель администратора</h2>
              <p>Сводка по задачам, выплатам, модерации и состоянию маркетплейса. На первом экране собраны действия, которые требуют внимания оператора.</p>
              <div className="admin-actions">
                <Link href="/admin/trainers/applications" className="admin-button">Заявки тренеров</Link>
                <Link href="/admin/moderation" className="admin-button admin-button--secondary">Модерация</Link>
                <Link href="/admin/payouts" className="admin-button admin-button--ghost">Выплаты</Link>
              </div>
            </div>
            <article className="admin-live-card">
              <span>Состояние очередей</span>
              <strong>{openModeration > 0 ? 'Есть задачи' : 'Все спокойно'}</strong>
              <div className="admin-status-line">
                <span className={statusDotClass(openModeration > 0 ? 'warning' : 'success')} />
                <small>{openModeration} задач на проверке</small>
              </div>
            </article>
          </section>

          {msg ? (
            <section className="admin-alert">
              <h3>Не удалось загрузить админ-панель</h3>
              <p>{msg}</p>
            </section>
          ) : null}
          {!state ? (
            <section className="admin-section">
              <h3>Загружаем данные</h3>
              <p>Получаем аналитику, выплаты, очереди модерации и отзывы на проверке.</p>
            </section>
          ) : null}

          {state ? (
            <>
              <section className="admin-metric-grid" aria-label="Admin metrics">
                <article className="admin-metric-card">
                  <span>Выручка за 30 дней</span>
                  <strong>{money(state.analytics?.revenue)}</strong>
                  <small>Оплаченные заказы маркетплейса</small>
                </article>
                <article className="admin-metric-card">
                  <span>Оплаченные заказы</span>
                  <strong>{state.analytics?.paid_orders || 0}</strong>
                  <small>За последние 30 дней</small>
                </article>
                <article className="admin-metric-card">
                  <span>Ожидает выплат</span>
                  <strong>{money(state.payouts?.ops.pending_exposure_amount)}</strong>
                  <small>Сумма под контролем оператора</small>
                </article>
                <article className="admin-metric-card">
                  <span>Открытая модерация</span>
                  <strong>{openModeration}</strong>
                  <small>Открытые, проверка и эскалация</small>
                </article>
              </section>

              <section className="admin-work-grid">
                <section className="admin-section">
                  <div className="admin-section__header">
                    <div>
                      <h3>Очереди модерации</h3>
                      <p>Задачи, которые требуют ручной проверки.</p>
                    </div>
                    <Link href="/admin/moderation" className="admin-button admin-button--secondary">Открыть</Link>
                  </div>
                  <div className="admin-work-list">
                    {(state.moderation?.queues || []).length === 0 ? <div className="admin-empty">Новых задач модерации нет.</div> : null}
                    {(state.moderation?.queues || []).map((queue) => (
                      <article className="admin-work-card" key={queue.queue}>
                        <div className="admin-work-card__row">
                          <span>{queue.queue}</span>
                          <span className="admin-status-line">
                            <span className={statusDotClass(queue.open > 0 ? 'warning' : 'success')} />
                            <small>{queue.open > 0 ? 'Есть задачи' : 'Чисто'}</small>
                          </span>
                        </div>
                        <strong>{queue.open} открыто / {queue.total} всего</strong>
                      </article>
                    ))}
                  </div>
                </section>

                <section className="admin-section">
                  <div className="admin-section__header">
                    <div>
                      <h3>Статусы выплат</h3>
                      <p>Распределение выплат по текущим статусам.</p>
                    </div>
                    <Link href="/admin/payouts" className="admin-button admin-button--secondary">К выплатам</Link>
                  </div>
                  {(state.payouts?.statuses || []).length ? (
                    <div className="admin-bar-chart" aria-label="Payout status chart">
                      {(state.payouts?.statuses || []).map((bucket) => (
                        <div className="admin-bar-row" key={bucket.status}>
                          <span>{bucket.status}</span>
                          <span className="admin-bar-track">
                            <span className={barFillClass(bucket.count, maxPayoutBucket)} />
                          </span>
                          <strong>{bucket.count}</strong>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="admin-empty">Операционная сводка выплат пока пустая.</div>
                  )}
                </section>

                <section className="admin-section">
                  <div className="admin-section__header">
                    <div>
                      <h3>Отзывы</h3>
                      <p>Отзывы, ожидающие решения администратора.</p>
                    </div>
                    <Link href="/admin/reviews" className="admin-button admin-button--secondary">К отзывам</Link>
                  </div>
                  <article className="admin-work-card">
                    <span>На проверке</span>
                    <strong>{state.reviews.length}</strong>
                    <div className="admin-status-line">
                      <span className={statusDotClass(state.reviews.length > 0 ? 'warning' : 'success')} />
                      <small>{state.reviews.length > 0 ? 'Нужно решение' : 'Очередь пустая'}</small>
                    </div>
                  </article>
                </section>
              </section>

              <section className="admin-section">
                <div className="admin-section__header">
                  <div>
                    <h3>Быстрые действия</h3>
                    <p>Частые переходы оператора без поиска в меню.</p>
                  </div>
                </div>
                <div className="admin-actions">
                  <Link href="/admin/trainers/applications" className="admin-button admin-button--secondary">Заявки тренеров</Link>
                  <Link href="/admin/reconciliation" className="admin-button admin-button--secondary">Сверка</Link>
                  <Link href="/admin/subscriptions" className="admin-button admin-button--secondary">Подписки</Link>
                  <Link href="/admin/settings/payments" className="admin-button admin-button--secondary">Настройки оплат</Link>
                </div>
              </section>
            </>
          ) : null}
        </section>
      )}
    </ProtectedPage>
  );
}
