'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { adminReconciliationSnapshotsApi } from '@/modules/admin-reconciliation-snapshots/api';
import type {
  ReconciliationSnapshot,
  SnapshotCompareIssue,
  SnapshotCompareResponse,
  SnapshotMetricsResponse,
  SnapshotRetentionResponse,
  SnapshotScheduleResponse,
  SnapshotSectionStatus,
  SnapshotSource,
  SnapshotStatus,
  SnapshotTrendPoint,
  SnapshotTrendResponse,
} from '@/modules/admin-reconciliation-snapshots/api';

export function label(value: string) {
  return value.replaceAll('_', ' ');
}

export function formatDate(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('ru-RU');
}

export function formatNumber(value: unknown) {
  const parsed = Number(value || 0);
  return Number.isFinite(parsed) ? parsed.toLocaleString('ru-RU') : '0';
}

export function numberValue(value: unknown) {
  const parsed = Number(value || 0);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function scalar(value: unknown, fallback = '—') {
  if (value === null || value === undefined || value === '') return fallback;
  if (typeof value === 'number') return value.toLocaleString('ru-RU');
  if (typeof value === 'boolean') return value ? 'yes' : 'no';
  if (Array.isArray(value)) return `${value.length} items`;
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

export function statusTitle(status?: SnapshotStatus) {
  if (!status) return 'Unknown';
  if (status === 'ok') return 'OK';
  if (status === 'degraded') return 'Degraded';
  if (status === 'critical') return 'Critical';
  if (status === 'missing') return 'Missing';
  if (status === 'failed') return 'Failed';
  return status;
}

export function sourceTitle(source?: SnapshotSource) {
  if (!source) return 'Any source';
  if (source === 'manual') return 'Manual';
  if (source === 'scheduled') return 'Scheduled';
  if (source === 'repair') return 'Repair';
  if (source === 'ci') return 'CI';
  return source;
}

function deltaLabel(value?: number) {
  const numeric = Number(value || 0);
  if (numeric > 0) return `+${numeric}`;
  return String(numeric);
}

function directionHint(direction?: string) {
  if (direction === 'improved') return 'Проблем стало меньше';
  if (direction === 'worsened') return 'Проблем стало больше';
  if (direction === 'unchanged') return 'Количество проблем не изменилось';
  if (direction === 'baseline') return 'Это базовый snapshot без сравнения';
  return 'Сравнение рассчитано backend service';
}

function badgeClass(status?: string) {
  if (status === 'ok' || status === 'improved') return 'badge success';
  if (status === 'critical' || status === 'failed' || status === 'worsened') return 'badge danger';
  if (status === 'degraded') return 'badge warning';
  return 'badge secondary';
}

function snapshotHref(snapshot?: ReconciliationSnapshot | null) {
  if (!snapshot?.id) return '#';
  return snapshot.href || `/admin/entities/reconciliation_snapshot/${snapshot.id}`;
}

function lastSegment(id?: string | null) {
  if (!id) return '—';
  return id.length > 12 ? id.slice(0, 8) : id;
}

function PanelHeader({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="row" style={{ alignItems: 'flex-start', marginBottom: 16 }}>
      <div>
        {eyebrow ? <span className="badge secondary">{eyebrow}</span> : null}
        <h2 style={{ marginTop: eyebrow ? 10 : 0 }}>{title}</h2>
        {description ? <p>{description}</p> : null}
      </div>
      {action ? <div className="inline">{action}</div> : null}
    </div>
  );
}

function StatCard({ title, value, hint, badge }: { title: string; value: ReactNode; hint?: string; badge?: ReactNode }) {
  return (
    <div className="card compact">
      <div className="row" style={{ alignItems: 'flex-start' }}>
        <div className="kpi">
          <small>{title}</small>
          <strong>{value}</strong>
          {hint ? <small>{hint}</small> : null}
        </div>
        {badge}
      </div>
    </div>
  );
}

function EmptyState({ children }: { children: ReactNode }) {
  return <div className="empty-state">{children}</div>;
}

function SectionMiniGrid({ sectionStatuses }: { sectionStatuses?: Record<string, SnapshotSectionStatus> }) {
  const rows = Object.entries(sectionStatuses || {});
  if (!rows.length) {
    return <EmptyState>Section statuses отсутствуют в последнем snapshot.</EmptyState>;
  }

  return (
    <div className="grid-3">
      {rows.map(([sectionKey, section]) => (
        <div className="card compact shadow-none" key={sectionKey}>
          <div className="row">
            <strong>{label(sectionKey)}</strong>
            <span className={badgeClass(section.status)}>{statusTitle(section.status)}</span>
          </div>
          <small>
            {formatNumber(section.issue_count ?? section.total_issues)} issues · {formatNumber(section.critical_count)} critical ·{' '}
            {formatNumber(section.warning_count)} warning
          </small>
        </div>
      ))}
    </div>
  );
}

export function ReconciliationHealthCard({
  latestSnapshot,
  metrics,
  schedule,
}: {
  latestSnapshot?: ReconciliationSnapshot | null;
  metrics?: SnapshotMetricsResponse | null;
  schedule?: SnapshotScheduleResponse | null;
}) {
  const headline = metrics?.headline;
  const current = latestSnapshot || null;
  const status = current?.status || headline?.latest_status || metrics?.status || 'missing';
  const totalIssues = current?.total_issues ?? headline?.latest_total_issues ?? 0;
  const criticalCount = current?.critical_count ?? headline?.latest_critical_count ?? 0;
  const totalDelta = headline?.total_issues_delta;
  const criticalDelta = headline?.critical_count_delta;

  return (
    <div className="card hero">
      <PanelHeader
        eyebrow="Health summary"
        title="Reconciliation health"
        description="Короткая сводка последнего сохраненного snapshot и scheduled capture состояния."
        action={current?.id ? <Link className="btn secondary sm" href={snapshotHref(current)}>Open snapshot</Link> : null}
      />

      <div className="grid-4">
        <StatCard title="Status" value={statusTitle(status)} hint={formatDate(current?.generated_at || headline?.latest_generated_at)} badge={<span className={badgeClass(status)}>{statusTitle(status)}</span>} />
        <StatCard title="Total issues" value={formatNumber(totalIssues)} hint={totalDelta !== undefined ? `${deltaLabel(totalDelta)} since previous` : 'latest snapshot'} />
        <StatCard title="Critical" value={formatNumber(criticalCount)} hint={criticalDelta !== undefined ? `${deltaLabel(criticalDelta)} critical delta` : 'critical issues'} />
        <StatCard title="Scheduled capture" value={schedule?.due ? 'Due' : 'Not due'} hint={schedule?.next_capture_due_at ? `next ${formatDate(schedule.next_capture_due_at)}` : schedule?.message || 'guarded by backend'} badge={<span className={badgeClass(schedule?.due ? 'degraded' : 'ok')}>{schedule?.due ? 'due' : 'ok'}</span>} />
      </div>

      <div style={{ marginTop: 20 }}>
        <SectionMiniGrid sectionStatuses={current?.section_statuses} />
      </div>
    </div>
  );
}

export function ReconciliationSnapshotTrend({ trend, metrics }: { trend?: SnapshotTrendResponse | null; metrics?: SnapshotMetricsResponse | null }) {
  const points = useMemo(() => {
    const trendPoints = trend?.points || [];
    const metricPoints = metrics?.trend?.points || [];
    return trendPoints.length ? trendPoints : metricPoints;
  }, [metrics, trend]);

  const visiblePoints = points.slice(-24);
  const maxIssues = Math.max(...visiblePoints.map((point) => numberValue(point.total_issues)), 1);

  return (
    <div className="card">
      <PanelHeader
        eyebrow="Trend"
        title="Snapshot trend"
        description="Динамика total/critical issues по последним manual, scheduled и repair snapshot'ам."
        action={trend?.delta ? <span className={badgeClass(trend.delta.direction)}>{trend.delta.direction}</span> : null}
      />

      {!visiblePoints.length ? (
        <EmptyState>Истории snapshot'ов пока нет. Создай manual snapshot или дождись scheduled capture.</EmptyState>
      ) : (
        <div className="stack">
          {visiblePoints.map((point: SnapshotTrendPoint) => {
            const width = Math.max(4, Math.round((numberValue(point.total_issues) / maxIssues) * 100));
            return (
              <div className="card compact shadow-none" key={point.id}>
                <div className="row">
                  <div>
                    <strong>{formatDate(point.generated_at)}</strong>
                    <p>
                      {sourceTitle(point.source)} · {statusTitle(point.status)} · critical {formatNumber(point.critical_count)}
                    </p>
                  </div>
                  <strong>{formatNumber(point.total_issues)} issues</strong>
                </div>
                <div style={{ height: 10, borderRadius: 999, background: 'var(--bg-muted)', overflow: 'hidden' }}>
                  <div style={{ width: `${width}%`, height: '100%', borderRadius: 999, background: 'var(--primary)' }} />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export function ReconciliationRepairImpact({ metrics, repairSnapshots }: { metrics?: SnapshotMetricsResponse | null; repairSnapshots: ReconciliationSnapshot[] }) {
  const repair = metrics?.repair_effectiveness;

  return (
    <div className="card">
      <PanelHeader
        eyebrow="Repair impact"
        title="Repair effectiveness"
        description="Показывает, помогают ли repair actions реально уменьшать число reconciliation проблем."
      />

      <div className="grid-4">
        <StatCard title="Repair snapshots" value={formatNumber(repair?.total ?? repairSnapshots.length)} hint="source=repair" />
        <StatCard title="Improved" value={formatNumber(repair?.improved)} hint="problem count decreased" badge={<span className="badge success">better</span>} />
        <StatCard title="Worsened" value={formatNumber(repair?.worsened)} hint="problem count increased" badge={<span className="badge danger">risk</span>} />
        <StatCard title="Unchanged" value={formatNumber(repair?.unchanged)} hint="no visible delta" />
      </div>

      <div className="divider" />

      {!repairSnapshots.length ? (
        <EmptyState>Repair snapshot'ов пока нет. Они появятся после audited repair action из reconciliation report.</EmptyState>
      ) : (
        <div className="stack">
          {repairSnapshots.slice(0, 5).map((snapshot) => {
            const delta = snapshot.delta;
            return (
              <div className="card compact shadow-none" key={snapshot.id}>
                <div className="row">
                  <div>
                    <strong>Repair snapshot {lastSegment(snapshot.id)}</strong>
                    <p>{formatDate(snapshot.generated_at)} · correlation {snapshot.correlation_id || '—'}</p>
                  </div>
                  <span className={badgeClass(delta?.direction)}>{delta?.direction || statusTitle(snapshot.status)}</span>
                </div>
                <small>
                  total {formatNumber(snapshot.total_issues)} · critical {formatNumber(snapshot.critical_count)}
                  {delta ? ` · delta ${deltaLabel(delta.total_issues_delta)}` : ''}
                </small>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function issueTitle(issue: SnapshotCompareIssue) {
  return issue.message || issue.code || issue.key || `${issue.entity_type || 'entity'}:${issue.entity_id || 'unknown'}`;
}

function IssueList({ title, rows, empty }: { title: string; rows?: SnapshotCompareIssue[]; empty: string }) {
  const list = rows || [];
  return (
    <div className="card compact shadow-none">
      <div className="row">
        <h3>{title}</h3>
        <span className="badge secondary">{list.length}</span>
      </div>
      {!list.length ? (
        <small>{empty}</small>
      ) : (
        <ul className="list">
          {list.slice(0, 8).map((issue, index) => (
            <li className="list-item" key={`${issue.key || issue.code || title}-${index}`}>
              <strong>{issueTitle(issue)}</strong>
              <small>
                {issue.section ? `${issue.section} · ` : ''}
                {issue.severity || issue.current_severity || issue.previous_severity || 'severity n/a'} · {issue.entity_type || 'entity'}:{issue.entity_id || '—'}
              </small>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function ReconciliationComparePanel({ snapshots }: { snapshots: ReconciliationSnapshot[] }) {
  const defaultCurrent = snapshots[0]?.id || '';
  const defaultBaseline = snapshots[1]?.id || '';
  const [baselineId, setBaselineId] = useState(defaultBaseline);
  const [currentId, setCurrentId] = useState(defaultCurrent);
  const [compare, setCompare] = useState<SnapshotCompareResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [msg, setMsg] = useState('');

  const runCompare = async () => {
    try {
      setIsLoading(true);
      setMsg('');
      setCompare(
        await adminReconciliationSnapshotsApi.compare({
          baseline_id: baselineId || undefined,
          current_id: currentId || undefined,
        })
      );
    } catch (error) {
      setMsg(error instanceof Error ? error.message : 'Не удалось сравнить snapshot\'ы');
    } finally {
      setIsLoading(false);
    }
  };

  const summary = compare?.summary;
  const direction = summary?.direction;

  return (
    <div className="card">
      <PanelHeader
        eyebrow="Compare"
        title="Snapshot comparison"
        description="Сравнение baseline/current показывает resolved, added и persisted issues после repair или scheduled capture."
        action={<button className="btn sm" type="button" disabled={isLoading || snapshots.length < 2} onClick={() => void runCompare()}>{isLoading ? 'Comparing...' : 'Compare'}</button>}
      />

      <div className="form-row">
        <label className="form-group">
          <span className="label">Baseline</span>
          <select className="select" value={baselineId} onChange={(event) => setBaselineId(event.target.value)}>
            <option value="">Auto baseline</option>
            {snapshots.map((snapshot) => (
              <option key={snapshot.id} value={snapshot.id}>
                {formatDate(snapshot.generated_at)} · {sourceTitle(snapshot.source)} · {lastSegment(snapshot.id)}
              </option>
            ))}
          </select>
        </label>
        <label className="form-group">
          <span className="label">Current</span>
          <select className="select" value={currentId} onChange={(event) => setCurrentId(event.target.value)}>
            <option value="">Auto current</option>
            {snapshots.map((snapshot) => (
              <option key={snapshot.id} value={snapshot.id}>
                {formatDate(snapshot.generated_at)} · {sourceTitle(snapshot.source)} · {lastSegment(snapshot.id)}
              </option>
            ))}
          </select>
        </label>
      </div>

      {msg ? <div className="card error compact">{msg}</div> : null}

      {compare ? (
        <>
          <div className="grid-4" style={{ marginTop: 16 }}>
            <StatCard title="Direction" value={direction || '—'} hint={directionHint(direction)} badge={direction ? <span className={badgeClass(direction)}>{direction}</span> : null} />
            <StatCard title="Issue delta" value={deltaLabel(summary?.total_issues_delta)} hint="current - baseline" />
            <StatCard title="Resolved" value={formatNumber(summary?.resolved_count ?? compare.resolved?.length)} hint="disappeared issues" />
            <StatCard title="Added" value={formatNumber(summary?.added_count ?? compare.added?.length)} hint="new issues" />
          </div>
          <div className="grid-3" style={{ marginTop: 16 }}>
            <IssueList title="Resolved" rows={compare.resolved} empty="Новых resolved issues нет." />
            <IssueList title="Added" rows={compare.added} empty="Новых added issues нет." />
            <IssueList title="Persisted" rows={compare.persisted} empty="Persisted issues нет." />
          </div>
        </>
      ) : (
        <EmptyState>Выбери два snapshot'а и нажми Compare. Если поля пустые, backend сравнит последние два snapshot'а автоматически.</EmptyState>
      )}
    </div>
  );
}

function retentionCount(value: SnapshotRetentionResponse | null, key: 'candidate_count' | 'deleted_count' | 'protected_count') {
  if (!value) return 0;
  const direct = numberValue(value[key]);
  if (direct) return direct;
  if (key === 'candidate_count') return (value.candidates || []).length;
  if (key === 'protected_count') return (value.protected_snapshots || value.protected || []).length;
  return 0;
}

export function ReconciliationRetentionPanel({ initialPreview, onChanged }: { initialPreview?: SnapshotRetentionResponse | null; onChanged: () => void }) {
  const [source, setSource] = useState('scheduled');
  const [keepMin, setKeepMin] = useState(5);
  const [confirmPrune, setConfirmPrune] = useState(false);
  const [preview, setPreview] = useState<SnapshotRetentionResponse | null>(initialPreview || null);
  const [isLoading, setIsLoading] = useState(false);
  const [msg, setMsg] = useState('');

  const payload = {
    dry_run: true,
    source: source || undefined,
    keep_min_per_source: keepMin,
  };

  const runPreview = async () => {
    try {
      setIsLoading(true);
      setMsg('');
      setPreview(await adminReconciliationSnapshotsApi.pruneRetention(payload));
    } catch (error) {
      setMsg(error instanceof Error ? error.message : 'Не удалось посчитать retention preview');
    } finally {
      setIsLoading(false);
    }
  };

  const runPrune = async () => {
    if (!confirmPrune) {
      setMsg('Подтверди prune: это удалит старые snapshot records согласно retention policy.');
      return;
    }

    try {
      setIsLoading(true);
      setMsg('');
      const result = await adminReconciliationSnapshotsApi.pruneRetention({ ...payload, dry_run: false });
      setPreview(result);
      setMsg(`Retention prune завершён. Deleted: ${retentionCount(result, 'deleted_count')}.`);
      setConfirmPrune(false);
      onChanged();
    } catch (error) {
      setMsg(error instanceof Error ? error.message : 'Retention prune failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card">
      <PanelHeader
        eyebrow="Retention"
        title="Snapshot retention"
        description="Безопасный preview/prune для ограничения роста таблицы reconciliation snapshots."
        action={
          <div className="inline">
            <button className="btn secondary sm" type="button" disabled={isLoading} onClick={() => void runPreview()}>{isLoading ? 'Loading...' : 'Preview'}</button>
            <button className="btn danger sm" type="button" disabled={isLoading} onClick={() => void runPrune()}>Prune</button>
          </div>
        }
      />

      <div className="form-row">
        <label className="form-group">
          <span className="label">Source</span>
          <select className="select" value={source} onChange={(event) => setSource(event.target.value)}>
            <option value="">All sources</option>
            <option value="scheduled">Scheduled</option>
            <option value="repair">Repair</option>
            <option value="manual">Manual</option>
            <option value="ci">CI</option>
          </select>
        </label>
        <label className="form-group">
          <span className="label">Keep min per source</span>
          <select className="select" value={keepMin} onChange={(event) => setKeepMin(Number(event.target.value))}>
            {[3, 5, 10, 20].map((value) => (
              <option key={value} value={value}>{value}</option>
            ))}
          </select>
        </label>
      </div>

      <label className="checkbox-inline" style={{ marginTop: 12 }}>
        <input type="checkbox" checked={confirmPrune} onChange={(event) => setConfirmPrune(event.target.checked)} />
        Подтверждаю prune старых snapshot records по retention policy
      </label>

      {msg ? <div className="card warning compact" style={{ marginTop: 12 }}>{msg}</div> : null}

      <div className="grid-3" style={{ marginTop: 16 }}>
        <StatCard title="Candidates" value={formatNumber(retentionCount(preview, 'candidate_count'))} hint="will be deleted on prune" />
        <StatCard title="Protected" value={formatNumber(retentionCount(preview, 'protected_count'))} hint="latest records kept" />
        <StatCard title="Deleted" value={formatNumber(retentionCount(preview, 'deleted_count'))} hint={preview?.dry_run === false ? 'last prune result' : 'dry-run mode'} />
      </div>
    </div>
  );
}

export function SnapshotHistoryPanel({ snapshots }: { snapshots: ReconciliationSnapshot[] }) {
  return (
    <div className="card">
      <PanelHeader eyebrow="History" title="Recent snapshots" description="Последние snapshot records с быстрым переходом в admin entity detail." />
      {!snapshots.length ? (
        <EmptyState>Snapshot history пустая. Нажми Capture snapshot, чтобы сохранить первое состояние.</EmptyState>
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Generated</th>
                <th>Source</th>
                <th>Status</th>
                <th>Issues</th>
                <th>Critical</th>
                <th>Correlation</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {snapshots.slice(0, 25).map((snapshot) => (
                <tr key={snapshot.id}>
                  <td>{formatDate(snapshot.generated_at)}</td>
                  <td>{sourceTitle(snapshot.source)}</td>
                  <td><span className={badgeClass(snapshot.status)}>{statusTitle(snapshot.status)}</span></td>
                  <td>{formatNumber(snapshot.total_issues)}</td>
                  <td>{formatNumber(snapshot.critical_count)}</td>
                  <td>{snapshot.correlation_id || '—'}</td>
                  <td><Link className="btn secondary sm" href={snapshotHref(snapshot)}>Open</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
