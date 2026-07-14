'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { isAdminUser } from '@/lib/authz';
import { privateApi } from '@/lib/api';
import type { AdminMarketplaceHealth, AuditEvent } from '@/types/api';

function money(value?: string | number | null, currency = 'RUB') {
  if (value === undefined || value === null || value === '') return `0 ${currency}`;
  return `${value} ${currency}`;
}

function statusBadge(status?: string) {
  if (status === 'healthy') return 'badge success';
  if (status === 'critical') return 'badge danger';
  if (status === 'warning') return 'badge warning';
  return 'badge secondary';
}

function asNumber(value: unknown): number {
  if (typeof value === 'number') return value;
  if (typeof value === 'string') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
  }
  return 0;
}

function formatDate(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('ru-RU');
}

function KpiCard({ label, value, hint, tone }: { label: string; value: string | number; hint?: string; tone?: 'warning' | 'danger' }) {
  return (
    <div className={tone ? `card ${tone}` : 'card'}>
      <div className="kpi">
        <span className="muted">{label}</span>
        <strong>{value}</strong>
        {hint ? <small>{hint}</small> : null}
      </div>
    </div>
  );
}

function AuditEventRow({ event }: { event: AuditEvent }) {
  return (
    <div className="list-item">
      <div className="stack" style={{ gap: 4 }}>
        <strong>{event.event_type}</strong>
        <small className="muted">{event.entity_type} · {event.entity_id}</small>
        <small className="muted">{event.actor_email || event.actor_id || 'system'} · {formatDate(event.created_at)}</small>
      </div>
      <span className="badge secondary">аудит</span>
    </div>
  );
}

export default function AdminMarketplaceCommandCenterPage() {
  const { user } = useAuthSession();
  const isAdmin = isAdminUser(user);
  const [days, setDays] = useState(30);
  const [health, setHealth] = useState<AdminMarketplaceHealth | null>(null);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');

  const summary = health?.summary;
  const topAlerts = useMemo(() => health?.alerts?.slice(0, 8) || [], [health]);
  const latestAudit = useMemo(() => (health?.audit.latest_events || auditEvents).slice(0, 8), [health, auditEvents]);

  async function load() {
    if (!isAdmin) return;
    try {
      setLoading(true);
      setMsg('');
      const [healthPayload, auditPayload] = await Promise.all([
        privateApi.getAdminMarketplaceHealth(days),
        privateApi.listAdminAuditEvents().catch(() => []),
      ]);
      setHealth(healthPayload);
      setAuditEvents(auditPayload);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить marketplace command center');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [isAdmin, days]);

  return (
    <ProtectedPage title="Центр маркетплейса" description="Единый центр состояния: модерация, выплаты, платежи, аналитика и журнал аудита.">
      {!isAdmin ? (
        <div className="card error">У текущей сессии нет роли администратора.</div>
      ) : (
        <section className="stack" style={{ gap: 24 }}>
          <div className="card dark">
            <div className="row" style={{ alignItems: 'flex-start' }}>
              <div className="stack" style={{ gap: 12 }}>
                <span className="badge secondary">Ядро маркетплейса v6.11</span>
                <h1 className="title-lg">Центр управления маркетплейсом</h1>
                <p className="lead">
                  Один экран для владельца платформы: здоровье бизнеса, очереди модерации, выплаты, failed payments и последние admin-actions.
                </p>
                <div className="inline" style={{ flexWrap: 'wrap' }}>
                  <Link href="/admin" className="button ghost">Главная админки</Link>
                  <Link href="/admin/moderation" className="button secondary">Модерация</Link>
                  <Link href="/admin/payouts" className="button secondary">Выплаты</Link>
                  <Link href="/admin/analytics" className="button secondary">Аналитика</Link>
                  <Link href="/admin/operations" className="button secondary">Операции</Link>
                </div>
              </div>
              <div className="stack" style={{ gap: 12, minWidth: 220 }}>
                <span className={statusBadge(health?.overall_status)}>{health?.overall_status || 'loading'}</span>
                <label className="label" htmlFor="marketplace-range">Период KPI</label>
                <select id="marketplace-range" className="select" value={days} onChange={(event) => setDays(Number(event.target.value))}>
                  <option value={7}>7 дней</option>
                  <option value={30}>30 дней</option>
                  <option value={90}>90 дней</option>
                  <option value={365}>365 дней</option>
                </select>
                <button type="button" className="button" disabled={loading} onClick={() => void load()}>{loading ? 'Обновление...' : 'Обновить'}</button>
              </div>
            </div>
          </div>

          {msg ? <div className="card error">{msg}</div> : null}
          {!health ? <div className="card">Загрузка состояния маркетплейса...</div> : null}

          {health && summary ? (
            <>
              <div className="grid-4">
                <KpiCard label="Выручка" value={money(summary.revenue)} hint={`${summary.paid_orders} paid orders`} />
                <KpiCard label="Открытая модерация" value={summary.open_moderation_cases} hint={`${summary.active_risk_flags} активных риск-флагов`} tone={summary.active_risk_flags ? 'warning' : undefined} />
                <KpiCard label="Ожидает выплат" value={money(summary.pending_payout_amount)} hint={`${summary.pending_payout_count} requests`} tone={summary.payout_reconciliation_issues ? 'warning' : undefined} />
                <KpiCard label="Ошибки оплат" value={summary.failed_payments} hint={`${days}d window`} tone={summary.failed_payments ? 'warning' : undefined} />
              </div>

              <div className="grid-4">
                <KpiCard label="Заявки тренеров" value={summary.under_review_applications} hint="на проверке" />
                <KpiCard label="Одобренные тренеры" value={summary.approved_trainers} />
                <KpiCard label="Отзывы на проверке" value={summary.pending_reviews} tone={summary.pending_reviews ? 'warning' : undefined} />
                <KpiCard label="Проблемы сверки" value={summary.payout_reconciliation_issues} tone={summary.payout_reconciliation_issues ? 'warning' : undefined} />
              </div>

              <div className="grid-2">
                <div className={topAlerts.length ? 'card warning' : 'card'}>
                  <div className="row">
                    <h2 className="title-md">Предупреждения системы</h2>
                    <span className={statusBadge(health.overall_status)}>{health.overall_status}</span>
                  </div>
                  <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                    {topAlerts.length === 0 ? <p className="muted">Критичных предупреждений нет.</p> : null}
                    {topAlerts.map((alert) => (
                      <div className="list-item" key={`${alert.section}-${alert.code}`}>
                        <div className="stack" style={{ gap: 4 }}>
                          <strong>{alert.code}</strong>
                          <small className="muted">{alert.message}</small>
                        </div>
                        <span className={statusBadge(alert.severity)}>{alert.section}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="card">
                  <div className="row">
                    <h2 className="title-md">Разделы системы</h2>
                    <small className="muted">Generated: {formatDate(health.generated_at)}</small>
                  </div>
                  <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                    {[
                      ['moderation', health.moderation.status],
                      ['trainer_onboarding', health.trainer_onboarding.status],
                      ['payouts', health.payouts.status],
                      ['payments', health.payments.status],
                      ['analytics', health.analytics.status],
                      ['reviews', health.reviews.status],
                      ['audit', health.audit.status],
                      ['system', String(health.system.status || 'healthy')],
                    ].map(([name, status]) => (
                      <div className="list-item" key={name}>
                        <span className="muted">{name}</span>
                        <span className={statusBadge(String(status))}>{status || 'unknown'}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="grid-3">
                <div className="card">
                  <h2 className="title-md">Очереди модерации</h2>
                  <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                    {(health.moderation.queues || []).length === 0 ? <p className="muted">Очередей нет.</p> : null}
                    {(health.moderation.queues || []).map((queue) => (
                      <div className="list-item" key={queue.queue}>
                        <span className="muted">{queue.queue}</span>
                        <strong>{queue.open} open / {queue.total} total</strong>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="card">
                  <h2 className="title-md">Онбординг тренеров</h2>
                  <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                    {(health.trainer_onboarding.status_counts || []).map((row) => (
                      <div className="list-item" key={row.status}>
                        <span className="muted">{row.status}</span>
                        <strong>{row.count}</strong>
                      </div>
                    ))}
                    <div className="list-item"><span className="muted">Отправлено без кейса</span><strong>{asNumber(health.trainer_onboarding.submitted_without_case)}</strong></div>
                    <div className="list-item"><span className="muted">Одобрено без роли</span><strong>{asNumber(health.trainer_onboarding.approved_without_role)}</strong></div>
                    <div className="list-item"><span className="muted">Одобрено без профиля</span><strong>{asNumber(health.trainer_onboarding.approved_without_profile)}</strong></div>
                  </div>
                </div>

                <div className="card">
                  <h2 className="title-md">Платежи</h2>
                  <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                    {(health.payments.statuses || []).map((row) => (
                      <div className="list-item" key={row.status}>
                        <span className="muted">{row.status}</span>
                        <strong>{row.count} · {money(row.amount)}</strong>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="grid-2">
                <div className="card">
                  <div className="row">
                    <h2 className="title-md">Последние события аудита</h2>
                    <Link href="/admin/operations" className="button ghost">Обслуживание</Link>
                  </div>
                  <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                    {latestAudit.length === 0 ? <p className="muted">Событий аудита пока нет.</p> : null}
                    {latestAudit.map((event) => <AuditEventRow event={event} key={event.id} />)}
                  </div>
                </div>

                <div className="card">
                  <h2 className="title-md">Счетчики действий</h2>
                  <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                    {(health.audit.action_counts || []).length === 0 ? <p className="muted">Счетчиков действий пока нет.</p> : null}
                    {(health.audit.action_counts || []).map((row) => (
                      <div className="list-item" key={row.event_type}>
                        <span className="muted">{row.event_type}</span>
                        <strong>{row.count}</strong>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </>
          ) : null}
        </section>
      )}
    </ProtectedPage>
  );
}
