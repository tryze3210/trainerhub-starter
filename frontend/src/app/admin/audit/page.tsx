'use client';

import Link from 'next/link';
import type { ReactNode } from 'react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { adminAuditApi, downloadAdminAuditCsv } from '@/modules/admin-audit/api';
import { adminEntityHref } from '@/modules/admin-entity-details/api';
import type { AuditEvent, AuditEventContext } from '@/modules/admin-audit/api';

const ACTION_PRESETS = [
  '',
  'admin.referrals.csv_export',
  'admin.outbox.dispatch',
  'admin.outbox.retry',
  'admin.outbox.mark_dead',
  'admin.outbox.requeue_stuck',
  'admin.payout_risk_hold.release',
  'admin.events.emit',
];

const ENTITY_PRESETS = [
  '',
  'referral_export',
  'outbox_message',
  'payment',
  'payout',
  'payout_request',
  'payment_webhook',
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

function Badge({ children }: { children: ReactNode }) {
  return (
    <span className="rounded-full border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-200">
      {children}
    </span>
  );
}

function StatCard({ title, value, hint }: { title: string; value: string | number; hint?: string }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4 shadow-sm">
      <p className="text-xs uppercase tracking-wide text-slate-500">{title}</p>
      <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
      {hint ? <p className="mt-1 text-xs text-slate-400">{hint}</p> : null}
    </div>
  );
}

function Field({ label: title, children }: { label: string; children: ReactNode }) {
  return (
    <label className="space-y-1 text-sm text-slate-300">
      <span className="block text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</span>
      {children}
    </label>
  );
}

function AuditEventCard({ event }: { event: AuditEvent }) {
  const contextJson = compactJson(event.context?.context || event.context || {});
  const correlationId = getCorrelationId(event.context);
  const targetHref = adminEntityHref(event.entity_type, event.entity_id);

  return (
    <article className="rounded-2xl border border-slate-800 bg-slate-950 p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-2">
          <div className="flex flex-wrap gap-2">
            <Badge>{getAction(event)}</Badge>
            <Badge>{getStatus(event)}</Badge>
            <Badge>{event.entity_type || 'entity'}</Badge>
          </div>
          <h2 className="text-lg font-semibold text-white">{event.event_type}</h2>
          <p className="text-sm text-slate-400">
            Target: {event.entity_type || '—'}:{event.entity_id || '—'}
          </p>
        </div>

        <div className="flex flex-wrap gap-2 text-sm">
          <Link
            href={`/admin/audit/${encodeURIComponent(event.id)}`}
            className="rounded-xl border border-slate-700 px-3 py-2 text-slate-200 hover:border-slate-500"
          >
            Open audit event
          </Link>
          {targetHref ? (
            <Link
              href={targetHref}
              className="rounded-xl border border-slate-700 px-3 py-2 text-slate-200 hover:border-slate-500"
            >
              Open target
            </Link>
          ) : null}
        </div>
      </div>

      <dl className="mt-5 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <dt className="text-slate-500">Created</dt>
          <dd className="text-slate-200">{formatDate(event.created_at)}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Actor</dt>
          <dd className="text-slate-200">{event.actor_email || 'system / unknown actor'}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Reason</dt>
          <dd className="text-slate-200">{scalar(getReason(event))}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Request</dt>
          <dd className="text-slate-200">{getRequestPath(event.context)}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Correlation</dt>
          <dd className="break-all text-slate-200">{correlationId || '—'}</dd>
        </div>
        <div>
          <dt className="text-slate-500">IP</dt>
          <dd className="text-slate-200">{event.ip_address || '—'}</dd>
        </div>
      </dl>

      {contextJson ? (
        <details className="mt-5 rounded-xl border border-slate-800 bg-slate-900/60 p-3 text-sm">
          <summary className="cursor-pointer text-slate-300">Показать context snapshot</summary>
          <pre className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap break-words text-xs text-slate-300">
            {contextJson}
          </pre>
        </details>
      ) : null}
    </article>
  );
}

export default function AdminAuditPage() {
  const { user } = useAuthSession();
  const isAdmin = user?.active_role === 'admin';

  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [eventType, setEventType] = useState('');
  const [entityType, setEntityType] = useState('');
  const [entityId, setEntityId] = useState('');
  const [actorId, setActorId] = useState('');
  const [createdFrom, setCreatedFrom] = useState('');
  const [createdTo, setCreatedTo] = useState('');
  const [search, setSearch] = useState('');
  const [limit, setLimit] = useState(100);
  const [isLoading, setIsLoading] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [msg, setMsg] = useState('');
  const [notice, setNotice] = useState('');

  const load = useCallback(async () => {
    if (!isAdmin) return;

    try {
      setIsLoading(true);
      setMsg('');
      setNotice('');

      const payload = await adminAuditApi.listEvents({
        event_type: eventType.trim() || undefined,
        entity_type: entityType.trim() || undefined,
        entity_id: entityId.trim() || undefined,
        actor_id: actorId.trim() || undefined,
        created_from: createdFrom || undefined,
        created_to: createdTo || undefined,
        search: search.trim() || undefined,
        limit,
      });

      setEvents(payload);
    } catch (error) {
      setMsg(error instanceof Error ? error.message : 'Не удалось загрузить audit feed');
    } finally {
      setIsLoading(false);
    }
  }, [actorId, createdFrom, createdTo, entityId, entityType, eventType, isAdmin, limit, search]);

  useEffect(() => {
    void load();
  }, [load]);

  const stats = useMemo(() => {
    const byAction = new Map<string, number>();
    const byEntity = new Map<string, number>();

    for (const event of events) {
      const action = String(getAction(event) || 'unknown');
      const entity = event.entity_type || 'unknown';

      byAction.set(action, (byAction.get(action) || 0) + 1);
      byEntity.set(entity, (byEntity.get(entity) || 0) + 1);
    }

    const topActions = Array.from(byAction.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8);
    const topEntities = Array.from(byEntity.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8);

    return { topActions, topEntities };
  }, [events]);

  function resetFilters() {
    setEventType('');
    setEntityType('');
    setEntityId('');
    setActorId('');
    setCreatedFrom('');
    setCreatedTo('');
    setSearch('');
    setLimit(100);
  }

  async function exportCsv() {
    try {
      setIsExporting(true);
      setMsg('');
      setNotice('');

      const filename = await downloadAdminAuditCsv({
        event_type: eventType.trim() || undefined,
        entity_type: entityType.trim() || undefined,
        entity_id: entityId.trim() || undefined,
        actor_id: actorId.trim() || undefined,
        created_from: createdFrom || undefined,
        created_to: createdTo || undefined,
        search: search.trim() || undefined,
      });

      setNotice(`CSV export downloaded: ${filename}`);
      void load();
    } catch (error) {
      setMsg(error instanceof Error ? error.message : 'Не удалось скачать audit CSV');
    } finally {
      setIsExporting(false);
    }
  }

  return (
    <ProtectedPage
      title="Admin audit feed"
      description="Audit trail for operational actions, reconciliation fixes and admin exports."
    >
      {!isAdmin ? (
        <div className="rounded-2xl border border-amber-800 bg-amber-950/40 p-6 text-amber-100">
          У текущей сессии нет admin-role.
        </div>
      ) : (
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">Audit trail</p>
              <h1 className="mt-2 text-3xl font-bold text-white">Admin audit feed</h1>
              <p className="mt-2 max-w-3xl text-slate-400">
                Кто, когда и что сделал в операционном контуре: retry outbox, mark dead, release risk hold,
                referral CSV export, reconciliation actions и ручной emit.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => void exportCsv()}
                disabled={isExporting}
                className="rounded-xl border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-100 hover:border-slate-500 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isExporting ? 'Export...' : 'Export CSV'}
              </button>
              <button
                type="button"
                onClick={() => void load()}
                className="rounded-xl bg-white px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-slate-200"
              >
                {isLoading ? 'Загрузка...' : 'Обновить'}
              </button>
            </div>
          </div>

          {msg ? (
            <div className="rounded-2xl border border-red-800 bg-red-950/40 p-4 text-sm text-red-100">{msg}</div>
          ) : null}

          {notice ? (
            <div className="rounded-2xl border border-emerald-800 bg-emerald-950/40 p-4 text-sm text-emerald-100">
              {notice}
            </div>
          ) : null}

          <section className="rounded-2xl border border-slate-800 bg-slate-950 p-5 shadow-sm">
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <Field label="Event type">
                <input
                  list="audit-event-presets"
                  value={eventType}
                  onChange={(event) => setEventType(event.target.value)}
                  placeholder="admin.referrals.csv_export"
                  className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-slate-400"
                />
                <datalist id="audit-event-presets">
                  {ACTION_PRESETS.filter(Boolean).map((preset) => (
                    <option key={preset} value={preset} />
                  ))}
                </datalist>
              </Field>

              <Field label="Entity type">
                <input
                  list="audit-entity-presets"
                  value={entityType}
                  onChange={(event) => setEntityType(event.target.value)}
                  placeholder="referral_export / payment / payout"
                  className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-slate-400"
                />
                <datalist id="audit-entity-presets">
                  {ENTITY_PRESETS.filter(Boolean).map((preset) => (
                    <option key={preset} value={preset} />
                  ))}
                </datalist>
              </Field>

              <Field label="Entity id">
                <input
                  value={entityId}
                  onChange={(event) => setEntityId(event.target.value)}
                  placeholder="UUID / external id"
                  className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-slate-400"
                />
              </Field>

              <Field label="Actor id">
                <input
                  value={actorId}
                  onChange={(event) => setActorId(event.target.value)}
                  placeholder="admin user UUID"
                  className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-slate-400"
                />
              </Field>

              <Field label="Created from">
                <input
                  type="date"
                  value={createdFrom}
                  onChange={(event) => setCreatedFrom(event.target.value)}
                  className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-slate-400"
                />
              </Field>

              <Field label="Created to">
                <input
                  type="date"
                  value={createdTo}
                  onChange={(event) => setCreatedTo(event.target.value)}
                  className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-slate-400"
                />
              </Field>

              <Field label="Search">
                <input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="email, path, correlation, reason"
                  className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-slate-400"
                />
              </Field>

              <Field label="Limit">
                <select
                  value={limit}
                  onChange={(event) => setLimit(Number(event.target.value))}
                  className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-slate-400"
                >
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                  <option value={250}>250</option>
                  <option value={500}>500</option>
                </select>
              </Field>
            </div>

            <div className="mt-4 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => void load()}
                className="rounded-xl border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-100 hover:border-slate-500"
              >
                Применить фильтр
              </button>
              <button
                type="button"
                onClick={() => void exportCsv()}
                disabled={isExporting}
                className="rounded-xl border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-100 hover:border-slate-500 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isExporting ? 'Export...' : 'Скачать CSV'}
              </button>
              <button
                type="button"
                onClick={resetFilters}
                className="rounded-xl border border-slate-800 px-4 py-2 text-sm text-slate-400 hover:border-slate-600 hover:text-slate-200"
              >
                Сбросить
              </button>
            </div>
          </section>

          <div className="grid gap-4 md:grid-cols-2">
            <StatCard title="Loaded events" value={events.length} hint="по текущему фильтру" />
            <StatCard title="Limit" value={limit} hint="backend hard-cap: 500" />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <section className="rounded-2xl border border-slate-800 bg-slate-950 p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-white">Actions</h2>
              <div className="mt-4 space-y-2">
                {stats.topActions.length === 0 ? (
                  <p className="text-sm text-slate-500">Пока нет audit events.</p>
                ) : null}
                {stats.topActions.map(([action, count]) => (
                  <div key={action} className="flex items-center justify-between rounded-xl bg-slate-900 px-3 py-2">
                    <span className="text-sm text-slate-300">{label(action)}</span>
                    <span className="text-sm font-semibold text-white">{count}</span>
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-2xl border border-slate-800 bg-slate-950 p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-white">Entity types</h2>
              <div className="mt-4 space-y-2">
                {stats.topEntities.length === 0 ? (
                  <p className="text-sm text-slate-500">Пока нет entity buckets.</p>
                ) : null}
                {stats.topEntities.map(([entity, count]) => (
                  <div key={entity} className="flex items-center justify-between rounded-xl bg-slate-900 px-3 py-2">
                    <span className="text-sm text-slate-300">{label(entity)}</span>
                    <span className="text-sm font-semibold text-white">{count}</span>
                  </div>
                ))}
              </div>
            </section>
          </div>

          <section className="space-y-4">
            {isLoading ? (
              <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5 text-slate-300">
                Загрузка audit feed...
              </div>
            ) : null}

            {!isLoading && events.length === 0 ? (
              <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5 text-slate-400">
                Audit events по текущему фильтру не найдены.
              </div>
            ) : null}

            {events.map((event) => (
              <AuditEventCard key={event.id} event={event} />
            ))}
          </section>
        </div>
      )}
    </ProtectedPage>
  );
}
