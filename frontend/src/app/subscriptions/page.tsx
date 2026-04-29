'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { subscriptionsApi, type SubscriptionCenter, type SubscriptionItem } from '@/modules/subscriptions/api';

function formatMoney(value?: string | number, currency = 'RUB'): string {
  if (value === undefined || value === null || value === '') return `— ${currency}`;
  return `${value} ${currency}`;
}

function formatDate(value?: string | null): string {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function getStatusLabel(status?: string): string {
  const value = (status || '').toLowerCase();
  if (value === 'active') return 'Активна';
  if (value === 'pending') return 'Ожидает оплаты';
  if (value === 'past_due') return 'Проблема оплаты';
  if (value === 'cancelled' || value === 'canceled') return 'Отменена';
  if (value === 'expired') return 'Истекла';
  return status || 'unknown';
}

function getStatusClass(status?: string): string {
  const value = (status || '').toLowerCase();
  if (value === 'active') return 'badge success';
  if (value === 'pending') return 'badge warning';
  if (value === 'past_due' || value === 'cancelled' || value === 'canceled' || value === 'expired') return 'badge danger';
  return 'badge secondary';
}

function getTitle(item: SubscriptionItem): string {
  return item.plan?.title || item.plan_name || item.title || 'Подписка';
}

export default function SubscriptionsPage() {
  const [center, setCenter] = useState<SubscriptionCenter | null>(null);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState('');

  async function load() {
    try {
      setLoading(true);
      setMsg('');
      setCenter(await subscriptionsApi.getCenter(30));
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить подписки');
    } finally {
      setLoading(false);
    }
  }

  async function cancelSubscription(id: string) {
    try {
      setMsg('');
      await subscriptionsApi.cancel(id, 'customer_self_service');
      await load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось отменить подписку');
    }
  }

  async function reactivateSubscription(id: string) {
    try {
      setMsg('');
      await subscriptionsApi.reactivate(id);
      await load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось включить автопродление');
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const summary = center?.summary;
  const items = useMemo(() => center?.items || [], [center]);

  return (
    <ProtectedPage title="Подписки" description="Коммерческий центр подписок пользователя.">
      <section className="stack" style={{ gap: 28 }}>
        <div className="row" style={{ alignItems: 'flex-start' }}>
          <div className="stack" style={{ gap: 10 }}>
            <span className="badge success">Recurring revenue</span>
            <h1>Подписки</h1>
            <p className="lead">
              Здесь виден жизненный цикл подписок: активность, доступы, период,
              проблемы оплаты, автопродление и отмена.
            </p>
          </div>
          <div className="inline">
            <button className="button secondary" onClick={() => void load()}>Обновить</button>
            <Link href="/customer/access" className="button ghost">Доступы</Link>
            <Link href="/cabinet" className="button ghost">Кабинет</Link>
          </div>
        </div>

        <div className="grid-4">
          <div className="card"><div className="kpi"><span className="muted">Всего</span><strong>{summary?.total_count ?? 0}</strong></div></div>
          <div className="card"><div className="kpi"><span className="muted">Активные</span><strong>{summary?.active_count ?? 0}</strong></div></div>
          <div className="card"><div className="kpi"><span className="muted">Автопродление</span><strong>{summary?.auto_renew_count ?? 0}</strong></div></div>
          <div className="card"><div className="kpi"><span className="muted">Оплачено за период</span><strong>{formatMoney(summary?.period_spend, summary?.currency || 'RUB')}</strong></div></div>
        </div>

        {msg ? (
          <div className="card error"><strong>Ошибка</strong><p className="muted">{msg}</p></div>
        ) : null}

        <div className="card">
          <div className="row">
            <div>
              <h2>Readiness</h2>
              <p className="muted">Быстрая диагностика subscription-доступа.</p>
            </div>
          </div>
          <div className="grid-3">
            {(center?.readiness || []).map((item) => (
              <div className="card compact" key={item.code}>
                <span className={item.done ? 'badge success' : 'badge warning'}>{item.done ? 'OK' : 'Need action'}</span>
                <strong>{item.label}</strong>
              </div>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="grid-2">
            {Array.from({ length: 4 }).map((_, idx) => (
              <div className="card" key={idx}><span className="badge">Загрузка</span><p className="muted">Получаем подписки...</p></div>
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="empty-state">
            <h3>Подписок пока нет</h3>
            <p>После оформления subscription checkout активные доступы появятся здесь.</p>
            <Link href="/catalog" className="button">Перейти в каталог</Link>
          </div>
        ) : (
          <div className="grid-2">
            {items.map((item) => (
              <article className="card" key={item.id}>
                <div className="stack" style={{ gap: 12 }}>
                  <div className="row">
                    <div>
                      <span className={getStatusClass(item.status)}>{getStatusLabel(item.status)}</span>
                      <h3>{getTitle(item)}</h3>
                      <p className="muted">{formatMoney(item.amount || item.plan?.price, item.currency || item.plan?.currency || 'RUB')} · {item.plan?.period_days || '—'} дней</p>
                    </div>
                    <strong>{item.remaining_days ?? '—'} дн.</strong>
                  </div>
                  <div className="divider" />
                  <div className="grid-2">
                    <p><span className="muted">Старт:</span><br />{formatDate(item.starts_at || item.started_at)}</p>
                    <p><span className="muted">Конец периода:</span><br />{formatDate(item.ends_at || item.current_period_end)}</p>
                    <p><span className="muted">Доступов:</span><br />{item.entitlement_count ?? 0}</p>
                    <p><span className="muted">Автопродление:</span><br />{item.auto_renew ? 'Включено' : 'Выключено'}</p>
                  </div>
                  {item.latest_payment ? (
                    <p className="muted">Последняя оплата: {item.latest_payment.status} · {formatMoney(item.latest_payment.amount, item.latest_payment.currency)}</p>
                  ) : null}
                  <div className="inline">
                    {item.status === 'active' ? (
                      <button className="button danger" onClick={() => void cancelSubscription(item.id)}>Отменить</button>
                    ) : null}
                    {item.status === 'cancelled' && item.remaining_days !== 0 ? (
                      <button className="button secondary" onClick={() => void reactivateSubscription(item.id)}>Возобновить</button>
                    ) : null}
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
