'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

import { ProtectedPage } from '@/components/protected-page';
import {
  subscriptionsApi,
  type SubscriptionCenter,
  type SubscriptionItem,
  type SubscriptionLifecyclePolicy,
} from '@/modules/subscriptions/api';

const DAY_OPTIONS = [7, 30, 90, 180];

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

function StatCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <article className="card stack" style={{ gap: 8 }}>
      <span className="muted">{label}</span>
      <strong className="title-md">{value}</strong>
      {hint ? <span className="muted">{hint}</span> : null}
    </article>
  );
}

function RenewalBlock({ item }: { item: SubscriptionItem }) {
  const projection = item.renewal_projection;
  if (!projection) return null;
  return (
    <div className="card muted-card stack" style={{ gap: 8 }}>
      <strong>Renewal projection</strong>
      <span className="muted">Причина: {projection.reason}</span>
      <span>Следующий период: {formatDate(projection.next_period_start)} → {formatDate(projection.next_period_end)}</span>
      <span>{formatMoney(projection.amount, projection.currency)}</span>
      <span className={projection.can_renew ? 'badge success' : 'badge warning'}>
        {projection.can_renew ? 'Готова к продлению' : 'Требует действия'}
      </span>
    </div>
  );
}

export default function SubscriptionsPage() {
  const [days, setDays] = useState(30);
  const [center, setCenter] = useState<SubscriptionCenter | null>(null);
  const [policy, setPolicy] = useState<SubscriptionLifecyclePolicy | null>(null);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState('');

  async function load(selectedDays = days) {
    try {
      setLoading(true);
      setMsg('');
      const [centerPayload, policyPayload] = await Promise.all([
        subscriptionsApi.getCenter(selectedDays),
        subscriptionsApi.getLifecyclePolicy(),
      ]);
      setCenter(centerPayload);
      setPolicy(policyPayload);
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

  async function resumeSubscription(id: string) {
    try {
      setMsg('');
      await subscriptionsApi.resume(id, 'customer_self_service_resume');
      await load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось возобновить подписку');
    }
  }

  async function syncSubscription(id: string) {
    try {
      setMsg('');
      const result = await subscriptionsApi.syncEntitlements(id, 'customer_manual_sync');
      setMsg(`Доступы синхронизированы: ${result.action}, active ${result.active_before} → ${result.active_after}`);
      await load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось синхронизировать доступы');
    }
  }

  useEffect(() => {
    void load(days);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days]);

  const summary = center?.summary;
  const lifecycleSummary = center?.lifecycle?.summary;
  const items = useMemo(() => center?.items || [], [center]);

  return (
    <ProtectedPage
      title="Подписки"
      description="Центр жизненного цикла подписок: активность, автопродление, проблемы оплаты, синхронизация доступов и прогноз следующего периода."
    >
      <main className="stack page-shell">
        <section className="hero card stack">
          <span className="eyebrow">Recurring revenue</span>
          <h1>Подписки</h1>
          <p className="muted">
            Центр жизненного цикла подписок: активность, автопродление, проблемы оплаты, синхронизация доступов и прогноз следующего периода.
          </p>
          <div className="actions-row">
            <button className="btn secondary" type="button" onClick={() => void load()} disabled={loading}>
              Обновить
            </button>
            <Link className="btn secondary" href="/entitlements">Доступы</Link>
            <Link className="btn secondary" href="/dashboard">Кабинет</Link>
            <select value={days} onChange={(event) => setDays(Number(event.target.value))}>
              {DAY_OPTIONS.map((option) => (
                <option key={option} value={option}>{option} дней</option>
              ))}
            </select>
          </div>
        </section>

        <section className="grid-4">
          <StatCard label="Всего" value={summary?.total_count ?? 0} />
          <StatCard label="Активные" value={summary?.active_count ?? 0} />
          <StatCard label="Автопродление" value={summary?.auto_renew_count ?? 0} />
          <StatCard label="Оплачено за период" value={formatMoney(summary?.period_spend, summary?.currency || 'RUB')} />
        </section>

        <section className="grid-4">
          <StatCard label="Due soon" value={lifecycleSummary?.due_soon_count ?? 0} hint="Заканчиваются за 7 дней" />
          <StatCard label="Expired due" value={lifecycleSummary?.expired_due_count ?? 0} hint="Нужно обслужить expire job" />
          <StatCard label="Payment issues" value={lifecycleSummary?.failed_payments_count ?? summary?.failed_payments_count ?? 0} />
          <StatCard label="Active entitlements" value={lifecycleSummary?.active_entitlement_count ?? 0} />
        </section>

        {msg ? (
          <section className="card stack">
            <strong>Сообщение</strong>
            <p className="muted">{msg}</p>
          </section>
        ) : null}

        <section className="grid-2">
          <article className="card stack">
            <h2>Readiness</h2>
            <p className="muted">Быстрая диагностика subscription-доступа.</p>
            {(center?.readiness || []).map((item) => (
              <div key={item.code} className="row between">
                <span>{item.label}</span>
                <span className={item.done ? 'badge success' : 'badge warning'}>{item.done ? 'OK' : 'Need action'}</span>
              </div>
            ))}
          </article>

          <article className="card stack">
            <h2>Lifecycle policy</h2>
            <p className="muted">v8.46 работает без миграций: только существующие persisted statuses.</p>
            <div className="chips">
              {(policy?.supported_statuses || []).map((status) => (
                <span key={status} className="badge secondary">{status}</span>
              ))}
            </div>
            <p className="muted">
              trialing/paused пока virtual statuses. Их нужно вводить отдельной миграцией после стабилизации текущего commerce flow.
            </p>
          </article>
        </section>

        <section className="card stack">
          <h2>Мои подписки</h2>
          {loading ? (
            <div className="grid-2">
              {Array.from({ length: 4 }).map((_, idx) => (
                <article key={idx} className="card muted-card stack">
                  <strong>Загрузка</strong>
                  <span className="muted">Получаем подписки...</span>
                </article>
              ))}
            </div>
          ) : items.length === 0 ? (
            <div className="empty-state">
              <h3>Подписок пока нет</h3>
              <p>После оформления subscription checkout активные доступы появятся здесь.</p>
              <Link className="btn primary" href="/catalog">Перейти в каталог</Link>
            </div>
          ) : (
            <div className="grid-2">
              {items.map((item) => (
                <article key={item.id} className="card stack">
                  <div className="row between">
                    <span className={getStatusClass(item.status)}>{getStatusLabel(item.status)}</span>
                    <span className="muted">{item.remaining_days ?? '—'} дн.</span>
                  </div>
                  <h3>{getTitle(item)}</h3>
                  <p className="muted">
                    {formatMoney(item.amount || item.plan?.price, item.currency || item.plan?.currency || 'RUB')} · {item.plan?.period_days || '—'} дней
                  </p>
                  <div className="grid-2 compact">
                    <span><strong>Старт:</strong><br />{formatDate(item.starts_at || item.started_at)}</span>
                    <span><strong>Конец периода:</strong><br />{formatDate(item.ends_at || item.current_period_end)}</span>
                    <span><strong>Доступов:</strong><br />{item.entitlement_count ?? 0}</span>
                    <span><strong>Автопродление:</strong><br />{item.auto_renew ? 'Включено' : 'Выключено'}</span>
                  </div>
                  {item.latest_payment ? (
                    <p className="muted">
                      Последняя оплата: {item.latest_payment.status} · {formatMoney(item.latest_payment.amount, item.latest_payment.currency)}
                    </p>
                  ) : null}
                  <RenewalBlock item={item} />
                  <div className="actions-row">
                    {item.lifecycle?.can_cancel || item.status === 'active' ? (
                      <button className="btn secondary" type="button" onClick={() => void cancelSubscription(item.id)}>
                        Отменить
                      </button>
                    ) : null}
                    {item.lifecycle?.can_resume || item.status === 'cancelled' ? (
                      <button className="btn primary" type="button" onClick={() => void resumeSubscription(item.id)}>
                        Возобновить
                      </button>
                    ) : null}
                    <button className="btn secondary" type="button" onClick={() => void syncSubscription(item.id)}>
                      Sync access
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </main>
    </ProtectedPage>
  );
}
