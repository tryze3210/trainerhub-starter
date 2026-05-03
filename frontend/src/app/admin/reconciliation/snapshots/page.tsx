'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { adminReconciliationSnapshotsApi } from '@/modules/admin-reconciliation-snapshots/api';
import type {
  ReconciliationSnapshot,
  SnapshotListResponse,
  SnapshotSource,
  SnapshotStatus,
  SnapshotTrendResponse,
} from '@/modules/admin-reconciliation-snapshots/api';

const STATUS_FILTERS = ['', 'ok', 'degraded', 'critical'];
const SOURCE_FILTERS = ['', 'manual', 'scheduled', 'repair', 'ci'];

function label(value: string) {
  return value.replaceAll('_', ' ');
}

function formatDate(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('ru-RU');
}

function formatNumber(value: number | undefined | null) {
  return Number(value || 0).toLocaleString('ru-RU');
}

function statusTitle(status: SnapshotStatus) {
  if (status === 'ok') return 'OK';
  if (status === 'degraded') return 'Degraded';
  if (status === 'critical') return 'Critical';
  if (status === 'missing') return 'Missing';
  return status;
}

function sourceTitle(source: SnapshotSource) {
  if (source === 'manual') return 'Manual';
  if (source === 'scheduled') return 'Scheduled';
  if (source === 'repair') return 'Repair';
  if (source === 'ci') return 'CI';
  return source;
}

function deltaValue(value?: number) {
  const numeric = Number(value || 0);
  if (numeric > 0) return `+${numeric}`;
  return String(numeric);
}

function Badge({ children }: { children: React.ReactNode }) {
  return <span className="badge secondary">{children}</span>;
}

function StatCard({ title, value, hint }: { title: string; value: React.ReactNode; hint?: string }) {
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

function TrendBars({ trend }: { trend: SnapshotTrendResponse | null }) {
  const points = trend?.points || [];
  if (!points.length) {
    return <div className="card"><p className="muted">Пока нет snapshot history для построения тренда.</p></div>;
  }

  const maxValue = Math.max(...points.map((point) => point.total_issues), 1);

  return (
    <div className="card">
      <div className="row" style={{ alignItems: 'flex-start', gap: 16 }}>
        <div className="stack" style={{ gap: 6 }}>
          <Badge>Trend</Badge>
          <h2 className="title-md">Reconciliation trend</h2>
          <p className="muted">Динамика количества расхождений по последним snapshot'ам.</p>
        </div>
        {trend?.delta ? <Badge>{trend.delta.direction}</Badge> : null}
      </div>

      <div className="stack" style={{ gap: 12, marginTop: 18 }}>
        {points.slice(-20).map((point) => {
          const width = Math.max(4, Math.round((point.total_issues / maxValue) * 100));
          return (
            <div className="stack" key={point.id} style={{ gap: 6 }}>
              <div className="row" style={{ gap: 12 }}>
                <span className="muted" style={{ minWidth: 160 }}>{formatDate(point.generated_at)}</span>
                <Badge>{sourceTitle(point.source)}</Badge>
                <strong>{formatNumber(point.total_issues)} issues</strong>
                <span className="muted">critical {formatNumber(point.critical_count)}</span>
              </div>
              <div style={{ height: 10, borderRadius: 999, background: 'rgba(148, 163, 184, 0.18)', overflow: 'hidden' }}>
                <div style={{ width: `${width}%`, height: '100%', borderRadius: 999, background: 'currentColor' }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function SectionStatusGrid({ snapshot }: { snapshot: ReconciliationSnapshot }) {
  const entries = Object.entries(snapshot.section_statuses || {});
  if (!entries.length) return <p className="muted">Section statuses отсутствуют.</p>;

  return (
    <div className="grid-3" style={{ marginTop: 14 }}>
      {entries.map(([sectionKey, section]) => (
        <div className="list-item" key={sectionKey}>
          <span className="muted">{label(sectionKey)}</span>
          <strong>{statusTitle(section?.status || 'missing')}</strong>
          <small className="muted">
            {formatNumber(section?.issue_count)} issues · {formatNumber(section?.critical_count)} critical
          </small>
        </div>
      ))}
    </div>
  );
}

function SnapshotCard({ snapshot }: { snapshot: ReconciliationSnapshot }) {
  const delta = snapshot.delta;
  const href = snapshot.href || `/admin/entities/reconciliation_snapshot/${snapshot.id}`;

  return (
    <div className="card">
      <div className="row" style={{ alignItems: 'flex-start', gap: 16 }}>
        <div className="stack" style={{ gap: 8 }}>
          <div className="inline" style={{ gap: 8, flexWrap: 'wrap' }}>
            <Badge>{statusTitle(snapshot.status)}</Badge>
            <Badge>{sourceTitle(snapshot.source)}</Badge>
            {delta ? <Badge>{delta.direction}</Badge> : null}
          </div>
          <h2 className="title-md">Snapshot {snapshot.id.slice(0, 8)}</h2>
          <p className="muted">Generated {formatDate(snapshot.generated_at)} · correlation {snapshot.correlation_id || '—'}</p>
        </div>
        <div className="inline" style={{ justifyContent: 'flex-end', flexWrap: 'wrap' }}>
          <Link href={href} className="button secondary">Open snapshot</Link>
          {snapshot.audit_event_href ? <Link href={snapshot.audit_event_href} className="button ghost">Audit</Link> : null}
        </div>
      </div>

      <div className="grid-4" style={{ marginTop: 16 }}>
        <StatCard title="Total" value={formatNumber(snapshot.total_issues)} hint="issues" />
        <StatCard title="Critical" value={formatNumber(snapshot.critical_count)} hint="blocking" />
        <StatCard title="Warning" value={formatNumber(snapshot.warning_count)} hint="needs review" />
        <StatCard title="Delta" value={deltaValue(delta?.total_issues_delta)} hint="vs previous" />
      </div>

      <SectionStatusGrid snapshot={snapshot} />
    </div>
  );
}

export default function AdminReconciliationSnapshotsPage() {
  const { user } = useAuthSession();
  const isAdmin = user?.active_role === 'admin';
  const [listPayload, setListPayload] = useState<SnapshotListResponse | null>(null);
  const [trend, setTrend] = useState<SnapshotTrendResponse | null>(null);
  const [limit, setLimit] = useState(30);
  const [source, setSource] = useState('');
  const [status, setStatus] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isCapturing, setIsCapturing] = useState(false);
  const [msg, setMsg] = useState('');

  const load = useCallback(async () => {
    if (!isAdmin) return;
    try {
      setIsLoading(true);
      setMsg('');
      const [listResponse, trendResponse] = await Promise.all([
        adminReconciliationSnapshotsApi.list({ limit, source, status }),
        adminReconciliationSnapshotsApi.trend({ limit: Math.max(2, Math.min(limit, 250)) }),
      ]);
      setListPayload(listResponse);
      setTrend(trendResponse);
    } catch (error) {
      setMsg(error instanceof Error ? error.message : 'Не удалось загрузить reconciliation snapshots');
    } finally {
      setIsLoading(false);
    }
  }, [isAdmin, limit, source, status]);

  useEffect(() => {
    void load();
  }, [load]);

  const capture = useCallback(async () => {
    if (!isAdmin) return;
    try {
      setIsCapturing(true);
      setMsg('');
      const snapshot = await adminReconciliationSnapshotsApi.capture({
        source: 'manual',
        limit: 100,
        correlation_id: `manual-${Date.now()}`,
      });
      setMsg(`Snapshot ${snapshot.id.slice(0, 8)} создан. Status: ${statusTitle(snapshot.status)}.`);
      await load();
    } catch (error) {
      setMsg(error instanceof Error ? error.message : 'Не удалось создать reconciliation snapshot');
    } finally {
      setIsCapturing(false);
    }
  }, [isAdmin, load]);

  const latest = listPayload?.summary;
  const snapshots = useMemo(() => listPayload?.snapshots || [], [listPayload]);

  return (
    <ProtectedPage title="Reconciliation snapshots" description="История reconciliation report, тренды и snapshot'ы после repair actions.">
      {!isAdmin ? (
        <div className="card error">У текущей сессии нет admin-role.</div>
      ) : (
        <section className="stack" style={{ gap: 24 }}>
          <div className="row" style={{ alignItems: 'flex-start' }}>
            <div className="stack" style={{ gap: 10 }}>
              <span className="badge secondary">Reconciliation history</span>
              <h1>Reconciliation snapshots</h1>
              <p className="lead">
                История состояния reconciliation: сколько было расхождений, стало ли меньше после repair actions,
                и какие секции остаются проблемными.
              </p>
            </div>
            <div className="inline" style={{ flexWrap: 'wrap', justifyContent: 'flex-end' }}>
              <Link href="/admin/reconciliation" className="button secondary">Live report</Link>
              <Link href="/admin/operations" className="button ghost">Operations</Link>
              <button className="button secondary" type="button" disabled={isLoading} onClick={() => void load()}>
                {isLoading ? 'Loading...' : 'Refresh'}
              </button>
              <button className="button" type="button" disabled={isCapturing} onClick={() => void capture()}>
                {isCapturing ? 'Capturing...' : 'Capture snapshot'}
              </button>
            </div>
          </div>

          {msg ? <div className="card">{msg}</div> : null}

          <div className="grid-4">
            <StatCard title="Latest status" value={statusTitle(latest?.latest_status || 'missing')} hint={formatDate(latest?.latest_generated_at)} />
            <StatCard title="Latest issues" value={formatNumber(latest?.latest_total_issues)} hint="total" />
            <StatCard title="Latest critical" value={formatNumber(latest?.latest_critical_count)} hint="blocking" />
            <StatCard title="Snapshots" value={formatNumber(latest?.snapshot_count)} hint="stored" />
          </div>

          <TrendBars trend={trend} />

          <div className="card">
            <div className="row" style={{ alignItems: 'flex-end', gap: 14 }}>
              <div className="field" style={{ minWidth: 160 }}>
                <label>Limit</label>
                <select value={limit} onChange={(event) => setLimit(Number(event.target.value))}>
                  {[10, 20, 30, 50, 100, 250].map((value) => <option value={value} key={value}>{value}</option>)}
                </select>
              </div>
              <div className="field" style={{ minWidth: 180 }}>
                <label>Source</label>
                <select value={source} onChange={(event) => setSource(event.target.value)}>
                  {SOURCE_FILTERS.map((value) => <option value={value} key={value}>{value ? sourceTitle(value) : 'Any source'}</option>)}
                </select>
              </div>
              <div className="field" style={{ minWidth: 180 }}>
                <label>Status</label>
                <select value={status} onChange={(event) => setStatus(event.target.value)}>
                  {STATUS_FILTERS.map((value) => <option value={value} key={value}>{value ? statusTitle(value) : 'Any status'}</option>)}
                </select>
              </div>
              <button className="button secondary" type="button" disabled={isLoading} onClick={() => void load()}>
                Apply filters
              </button>
            </div>
          </div>

          <div className="stack" style={{ gap: 16 }}>
            <div className="row">
              <h2 className="title-md">Snapshot history</h2>
              <span className="muted">{snapshots.length} rows</span>
            </div>
            {snapshots.length ? snapshots.map((snapshot) => (
              <SnapshotCard snapshot={snapshot} key={snapshot.id} />
            )) : (
              <div className="card">
                <p className="muted">Snapshot'ов пока нет. Нажми Capture snapshot, чтобы сохранить первое состояние.</p>
              </div>
            )}
          </div>
        </section>
      )}
    </ProtectedPage>
  );
}
