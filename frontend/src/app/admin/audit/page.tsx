'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { adminAuditApi } from '@/modules/admin-audit/api';
import { adminEntityHref } from '@/modules/admin-entity-details/api';
import type { AuditEvent, AuditEventContext } from '@/modules/admin-audit/api';

const ACTION_PRESETS = [
  '',
  'admin.outbox.dispatch',
  'admin.outbox.retry',
  'admin.outbox.mark_dead',
  'admin.outbox.requeue_stuck',
  'admin.payout_risk_hold.release',
  'admin.events.emit',
];

function label(value: string) {
  return value.replaceAll('_', ' ');
}

function formatDate(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('ru-RU');
}

function scalar(value: unknown, fallback = '—') {
  if (value === null || value === undefined || value === '') return fallback;
  if (typeof value === 'number') return value.toLocaleString('ru-RU');
  if (typeof value === 'boolean') return value ? 'yes' : 'no';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

function compactJson(value: unknown) {
  if (!value || typeof value !== 'object') return '';
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function getAction(event: AuditEvent) {
  return event.context?.action || event.event_type.replace(/^admin\./, '');
}

function getStatus(event: AuditEvent) {
  return event.context?.status || 'recorded';
}

function getReason(event: AuditEvent) {
  return event.context?.reason || '';
}

function getRequestPath(context?: AuditEventContext | null) {
  const method = context?.request?.method || '';
  const path = context?.request?.path || '';
  if (!method && !path) return '—';
  return `${method} ${path}`.trim();
}

function getCorrelationId(context?: AuditEventContext | null) {
  return context?.request?.correlation_id || '';
}

function Badge({ children }: { children: React.ReactNode }) {
  return <span className="badge secondary">{children}</span>;
}

function StatCard({ title, value, hint }: { title: string; value: string | number; hint?: string }) {
  return (
    <div className="card">
      <div className="kpi">
        <span className="muted">{title}</span>
        <strong>{value}</strong>
        {hint ? <small className="muted">{hint}</small> : null}
      </div>
    </div>
  );
}

function AuditEventCard({ event }: { event: AuditEvent }) {
  const contextJson = compactJson(event.context?.context || event.context || {});
  const correlationId = getCorrelationId(event.context);

  return (
    <div className="card">
      <div className="row" style={{ alignItems: 'flex-start', gap: 16 }}>
        <div className="stack" style={{ gap: 8 }}>
          <div className="inline" style={{ gap: 8, flexWrap: 'wrap' }}>
            <Badge>{getAction(event)}</Badge>
            <Badge>{getStatus(event)}</Badge>
            <Badge>{event.entity_type || 'entity'}</Badge>
          </div>
          <h2 className="title-md">{event.event_type}</h2>
          <p className="muted">
            Target: <strong>{event.entity_type}:{event.entity_id}</strong>
          </p>
          <div className="inline" style={{ gap: 8, flexWrap: 'wrap' }}>
            <Link href={adminEntityHref('audit_event', event.id)} className="button secondary">Open audit event</Link>
            {event.entity_type && event.entity_id ? (
              <Link href={adminEntityHref(event.entity_type, event.entity_id)} className="button ghost">Open target</Link>
            ) : null}
          </div>
        </div>
        <div className="stack" style={{ gap: 6, textAlign: 'right' }}>
          <strong>{formatDate(event.created_at)}</strong>
          <span className="muted">{event.actor_email || 'system / unknown actor'}</span>
        </div>
      </div>

      <div className="grid-4" style={{ marginTop: 16 }}>
        <div className="list-item"><span className="muted">Reason</span><strong>{scalar(getReason(event))}</strong></div>
        <div className="list-item"><span className="muted">Request</span><strong>{getRequestPath(event.context)}</strong></div>
        <div className="list-item"><span className="muted">Correlation</span><strong>{correlationId || '—'}</strong></div>
        <div className="list-item"><span className="muted">IP</span><strong>{event.ip_address || '—'}</strong></div>
      </div>

      {contextJson ? (
        <details style={{ marginTop: 16 }}>
          <summary className="muted" style={{ cursor: 'pointer' }}>Показать context snapshot</summary>
          <pre className="card" style={{ overflowX: 'auto', marginTop: 12, whiteSpace: 'pre-wrap' }}>{contextJson}</pre>
        </details>
      ) : null}
    </div>
  );
}

export default function AdminAuditPage() {
  const { user } = useAuthSession();
  const isAdmin = user?.active_role === 'admin';
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [eventType, setEventType] = useState('');
  const [entityType, setEntityType] = useState('');
  const [entityId, setEntityId] = useState('');
  const [limit, setLimit] = useState(100);
  const [isLoading, setIsLoading] = useState(false);
  const [msg, setMsg] = useState('');

  const load = useCallback(async () => {
    if (!isAdmin) return;
    try {
      setIsLoading(true);
      setMsg('');
      const payload = await adminAuditApi.listEvents({
        event_type: eventType.trim() || undefined,
        entity_type: entityType.trim() || undefined,
        entity_id: entityId.trim() || undefined,
        limit,
      });
      setEvents(payload);
    } catch (error) {
      setMsg(error instanceof Error ? error.message : 'Не удалось загрузить audit feed');
    } finally {
      setIsLoading(false);
    }
  }, [entityId, entityType, eventType, isAdmin, limit]);

  useEffect(() => {
    void load();
  }, [load]);

  const stats = useMemo(() => {
    const byAction = new Map<string, number>();
    const byEntity = new Map<string, number>();
    for (const event of events) {
      const action = String(getAction(event) || 'unknown');
      byAction.set(action, (byAction.get(action) || 0) + 1);
      byEntity.set(event.entity_type || 'unknown', (byEntity.get(event.entity_type || 'unknown') || 0) + 1);
    }
    const topActions = Array.from(byAction.entries()).sort((a, b) => b[1] - a[1]).slice(0, 8);
    const topEntities = Array.from(byEntity.entries()).sort((a, b) => b[1] - a[1]).slice(0, 8);
    return { topActions, topEntities };
  }, [events]);

  return (
    <ProtectedPage title="Admin audit" description="Audit feed операторских действий: outbox, webhooks, payout holds и ручные операции администратора.">
      {!isAdmin ? (
        <div className="card error">У текущей сессии нет admin-role.</div>
      ) : (
        <section className="stack" style={{ gap: 24 }}>
          <div className="row" style={{ alignItems: 'flex-start' }}>
            <div className="stack" style={{ gap: 10 }}>
              <span className="badge secondary">Audit trail</span>
              <h1>Admin audit feed</h1>
              <p className="lead">Кто, когда и что сделал в операционном контуре: retry outbox, mark dead, release risk hold, requeue stuck и ручной emit.</p>
            </div>
            <div className="inline" style={{ flexWrap: 'wrap', justifyContent: 'flex-end' }}>
              <Link href="/admin/operations" className="button secondary">Operations</Link>
              <button className="button" type="button" disabled={isLoading} onClick={() => void load()}>
                {isLoading ? 'Загрузка...' : 'Обновить'}
              </button>
            </div>
          </div>

          {msg ? <div className="card error">{msg}</div> : null}

          <div className="card">
            <div className="grid-4">
              <label className="stack" style={{ gap: 6 }}>
                <span className="muted">Event type</span>
                <select className="select" value={eventType} onChange={(event) => setEventType(event.target.value)}>
                  {ACTION_PRESETS.map((preset) => (
                    <option key={preset || 'all'} value={preset}>{preset || 'all admin events'}</option>
                  ))}
                </select>
              </label>
              <label className="stack" style={{ gap: 6 }}>
                <span className="muted">Entity type</span>
                <input className="input" value={entityType} onChange={(event) => setEntityType(event.target.value)} placeholder="outbox_message / payment / payout" />
              </label>
              <label className="stack" style={{ gap: 6 }}>
                <span className="muted">Entity id</span>
                <input className="input" value={entityId} onChange={(event) => setEntityId(event.target.value)} placeholder="UUID / external id" />
              </label>
              <label className="stack" style={{ gap: 6 }}>
                <span className="muted">Limit</span>
                <select className="select" value={limit} onChange={(event) => setLimit(Number(event.target.value))}>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                  <option value={250}>250</option>
                  <option value={500}>500</option>
                </select>
              </label>
            </div>
            <div className="inline" style={{ marginTop: 16 }}>
              <button className="button" type="button" disabled={isLoading} onClick={() => void load()}>Применить фильтр</button>
              <button
                className="button ghost"
                type="button"
                disabled={isLoading}
                onClick={() => {
                  setEventType('');
                  setEntityType('');
                  setEntityId('');
                  setLimit(100);
                }}
              >
                Сбросить
              </button>
            </div>
          </div>

          <div className="grid-4">
            <StatCard title="Events loaded" value={events.length} hint="по текущему фильтру" />
            <StatCard title="Top action" value={stats.topActions[0]?.[0] || '—'} hint={stats.topActions[0] ? `${stats.topActions[0][1]} events` : 'нет данных'} />
            <StatCard title="Top entity" value={stats.topEntities[0]?.[0] || '—'} hint={stats.topEntities[0] ? `${stats.topEntities[0][1]} events` : 'нет данных'} />
            <StatCard title="Latest event" value={formatDate(events[0]?.created_at)} />
          </div>

          <div className="grid-2">
            <div className="card">
              <h2 className="title-md">Actions</h2>
              <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                {stats.topActions.length === 0 ? <p className="muted">Пока нет audit events.</p> : null}
                {stats.topActions.map(([action, count]) => (
                  <div className="list-item" key={action}>
                    <span className="muted">{label(action)}</span>
                    <strong>{count}</strong>
                  </div>
                ))}
              </div>
            </div>
            <div className="card">
              <h2 className="title-md">Entity types</h2>
              <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                {stats.topEntities.length === 0 ? <p className="muted">Пока нет entity buckets.</p> : null}
                {stats.topEntities.map(([entity, count]) => (
                  <div className="list-item" key={entity}>
                    <span className="muted">{label(entity)}</span>
                    <strong>{count}</strong>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="stack" style={{ gap: 16 }}>
            {isLoading ? <div className="card">Загрузка audit feed...</div> : null}
            {!isLoading && events.length === 0 ? <div className="card">Audit events по текущему фильтру не найдены.</div> : null}
            {events.map((event) => <AuditEventCard key={event.id} event={event} />)}
          </div>
        </section>
      )}
    </ProtectedPage>
  );
}
