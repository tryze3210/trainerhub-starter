'use client';

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import { useAuthSession } from '@/components/auth-provider';
import { isAdminUser } from '@/lib/authz';
import {
  adminSubscriptionsApi,
  type AdminSubscriptionItem,
  type SubscriptionRenewalProjection,
} from '@/modules/admin-subscriptions/api';

function formatDate(value?: string | null): string {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function money(value?: string | number | null, currency = 'RUB'): string {
  if (value === undefined || value === null || value === '') return `0 ${currency}`;
  return `${value} ${currency}`;
}

function planTitle(item: AdminSubscriptionItem | null): string {
  return item?.plan?.title || item?.plan_name || item?.title || 'Subscription';
}

export function AdminSubscriptionDetailPage({ subscriptionId }: { subscriptionId: string }) {
  const { user } = useAuthSession();
  const isAdmin = isAdminUser(user);

  const [item, setItem] = useState<AdminSubscriptionItem | null>(null);
  const [projection, setProjection] = useState<SubscriptionRenewalProjection | null>(null);
  const [reason, setReason] = useState('manual_admin_subscription_detail_ops');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!isAdmin) return;
    try {
      setLoading(true);
      setMessage('');
      const [subscriptionPayload, projectionPayload] = await Promise.all([
        adminSubscriptionsApi.getItem(subscriptionId),
        adminSubscriptionsApi.getRenewalProjection(subscriptionId),
      ]);
      setItem(subscriptionPayload);
      setProjection(projectionPayload);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Не удалось загрузить подписку.');
    } finally {
      setLoading(false);
    }
  }, [isAdmin, subscriptionId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function run(operation: string, action: () => Promise<unknown>, successMessage: string) {
    try {
      setBusy(operation);
      setMessage('');
      await action();
      setMessage(successMessage);
      await load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Операция не выполнена.');
    } finally {
      setBusy(null);
    }
  }

  if (!isAdmin) {
    return (
      <section className="page-shell stack">
        <div className="card empty-state">
          <span className="eyebrow">Только администратор</span>
          <h1>Детали подписки недоступен</h1>
          <p>Для просмотра нужна прав администратора.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="page-shell stack">
      <section className="hero card stack">
        <div className="row">
          <div>
            <span className="eyebrow">Детали подписки</span>
            <h1>{loading ? 'Загрузка подписки…' : planTitle(item)}</h1>
            <p>Аудит жизненного цикла, прогноз продления и синхронизация доступов по конкретной подписке.</p>
          </div>
          <div className="inline" style={{ flexWrap: 'wrap' }}>
            <button className="button secondary" disabled={loading} onClick={() => void load()}>
              Обновить
            </button>
            <Link className="button ghost" href="/admin/subscriptions">
              Ко всем подпискам
            </Link>
          </div>
        </div>
        {message ? <div className="card compact">{message}</div> : null}
      </section>

      {item ? (
        <>
          <section className="grid-4">
            <div className="card stat-card">
              <span className="muted">Статус</span>
              <strong>{item.status || '—'}</strong>
              <small>{item.is_active ? 'активна' : 'не активна'}</small>
            </div>
            <div className="card stat-card">
              <span className="muted">Сумма</span>
              <strong>{money(item.amount || item.price_amount || item.plan?.price, item.currency || item.plan?.currency || 'RUB')}</strong>
              <small>{item.plan?.period_days ? `${item.plan.period_days} дней` : 'период неизвестен'}</small>
            </div>
            <div className="card stat-card">
              <span className="muted">Конец периода</span>
              <strong>{formatDate(item.current_period_end || item.ends_at)}</strong>
              <small>{item.remaining_days ?? '—'} дней осталось</small>
            </div>
            <div className="card stat-card">
              <span className="muted">Доступы</span>
              <strong>{item.entitlement_count ?? '—'}</strong>
              <small>выданные доступы</small>
            </div>
          </section>

          <section className="grid-2">
            <div className="card stack">
              <h3>Идентификатор подписки</h3>
              <div className="grid-2">
                <div className="list-item"><span className="muted">ID</span><strong>{item.id}</strong></div>
                <div className="list-item"><span className="muted">Пользователь</span><strong>{item.user_id || item.customer_id || '—'}</strong></div>
                <div className="list-item"><span className="muted">Старт</span><strong>{formatDate(item.starts_at || item.started_at)}</strong></div>
                <div className="list-item"><span className="muted">Отменена</span><strong>{formatDate(item.cancelled_at || item.canceled_at || item.cancel_at)}</strong></div>
                <div className="list-item"><span className="muted">Автопродление</span><strong>{item.auto_renew ? 'yes' : 'no'}</strong></div>
                <div className="list-item"><span className="muted">Обновлено</span><strong>{formatDate(item.updated_at)}</strong></div>
              </div>
            </div>

            <div className="card stack">
              <h3>Прогноз продления</h3>
              <div className="grid-2">
                <div className="list-item"><span className="muted">Будет продлена</span><strong>{projection?.will_renew ? 'yes' : 'no'}</strong></div>
                <div className="list-item"><span className="muted">Следующее продление</span><strong>{formatDate(projection?.next_renewal_at)}</strong></div>
                <div className="list-item"><span className="muted">Сумма</span><strong>{money(projection?.amount, projection?.currency || item.currency || 'RUB')}</strong></div>
                <div className="list-item"><span className="muted">Автопродление</span><strong>{projection?.auto_renew ? 'yes' : 'no'}</strong></div>
              </div>
              {projection?.reasons?.length ? (
                <div className="stack compact">
                  {projection.reasons.map((reasonItem) => (
                    <div className="list-item" key={reasonItem}>{reasonItem}</div>
                  ))}
                </div>
              ) : null}
            </div>
          </section>

          <section className="card stack">
            <h3>Действия жизненного цикла</h3>
            <p className="muted">Каждое действие должно попадать в журнал аудита backend и сохранять причину.</p>
            <label className="stack compact">
              <span className="muted">Причина / заметка аудита</span>
              <input value={reason} onChange={(event) => setReason(event.target.value)} />
            </label>
            <div className="inline" style={{ flexWrap: 'wrap' }}>
              <button
                className="button secondary"
                disabled={!!busy || item.status === 'past_due'}
                onClick={() =>
                  void run(
                    'past-due',
                    () => adminSubscriptionsApi.markPastDue(item.id, reason),
                    'Подписка переведена в past_due.',
                  )
                }
              >
                Mark past due
              </button>
              <button
                className="button"
                disabled={!!busy}
                onClick={() =>
                  void run(
                    'sync',
                    () => adminSubscriptionsApi.syncEntitlements(item.id, reason),
                    'Entitlements синхронизированы.',
                  )
                }
              >
                Sync entitlements
              </button>
            </div>
          </section>
        </>
      ) : !loading ? (
        <div className="card empty-state">
          <h3>Подписка не найдена</h3>
          <p>Сервер не вернул детали подписки для этого id.</p>
        </div>
      ) : null}
    </section>
  );
}
