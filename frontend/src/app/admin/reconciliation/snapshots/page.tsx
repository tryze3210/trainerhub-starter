'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { adminReconciliationSnapshotsApi } from '@/modules/admin-reconciliation-snapshots/api';
import type {
  ReconciliationSnapshot,
  SnapshotListResponse,
  SnapshotMetricsResponse,
  SnapshotRetentionResponse,
  SnapshotScheduleResponse,
  SnapshotSource,
  SnapshotStatus,
  SnapshotTrendResponse,
} from '@/modules/admin-reconciliation-snapshots/api';
import {
  ReconciliationComparePanel,
  ReconciliationHealthCard,
  ReconciliationRepairImpact,
  ReconciliationRetentionPanel,
  ReconciliationSnapshotTrend,
  SnapshotHistoryPanel,
  formatDate,
  sourceTitle,
  statusTitle,
} from '@/modules/admin-reconciliation-snapshots/components/reconciliation-dashboard';

const STATUS_FILTERS: SnapshotStatus[] = ['', 'ok', 'degraded', 'critical', 'failed'];
const SOURCE_FILTERS: SnapshotSource[] = ['', 'manual', 'scheduled', 'repair', 'ci'];

function latestFromPayload(payload: SnapshotListResponse | null): ReconciliationSnapshot | null {
  return payload?.snapshots?.[0] || null;
}

export default function AdminReconciliationSnapshotsPage() {
  const { user } = useAuthSession();
  const isAdmin = user?.active_role === 'admin';

  const [listPayload, setListPayload] = useState<SnapshotListResponse | null>(null);
  const [repairPayload, setRepairPayload] = useState<SnapshotListResponse | null>(null);
  const [trend, setTrend] = useState<SnapshotTrendResponse | null>(null);
  const [metrics, setMetrics] = useState<SnapshotMetricsResponse | null>(null);
  const [schedule, setSchedule] = useState<SnapshotScheduleResponse | null>(null);
  const [retentionPreview, setRetentionPreview] = useState<SnapshotRetentionResponse | null>(null);

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

      const [listResponse, repairResponse, trendResponse, metricsResponse, scheduleResponse, retentionResponse] = await Promise.all([
        adminReconciliationSnapshotsApi.list({ limit, source, status }),
        adminReconciliationSnapshotsApi.list({ limit: 10, source: 'repair' }).catch(() => null),
        adminReconciliationSnapshotsApi.trend({ limit: Math.max(2, Math.min(limit, 250)) }).catch(() => null),
        adminReconciliationSnapshotsApi.metrics({ limit: Math.max(2, Math.min(limit, 250)), source, status }).catch(() => null),
        adminReconciliationSnapshotsApi.schedule({ source: 'scheduled', min_age_minutes: 60 }).catch(() => null),
        adminReconciliationSnapshotsApi.retention({ dry_run: true, source: 'scheduled', keep_min_per_source: 5 }).catch(() => null),
      ]);

      setListPayload(listResponse);
      setRepairPayload(repairResponse);
      setTrend(trendResponse);
      setMetrics(metricsResponse);
      setSchedule(scheduleResponse);
      setRetentionPreview(retentionResponse);
    } catch (error) {
      setMsg(error instanceof Error ? error.message : 'Не удалось загрузить reconciliation dashboard');
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
        correlation_id: `manual-dashboard-${Date.now()}`,
      });
      setMsg(`Snapshot ${snapshot.id.slice(0, 8)} создан. Status: ${statusTitle(snapshot.status)}.`);
      await load();
    } catch (error) {
      setMsg(error instanceof Error ? error.message : 'Не удалось создать reconciliation snapshot');
    } finally {
      setIsCapturing(false);
    }
  }, [isAdmin, load]);

  const snapshots = useMemo(() => listPayload?.snapshots || [], [listPayload]);
  const repairSnapshots = useMemo(() => repairPayload?.snapshots || [], [repairPayload]);
  const latestSnapshot = latestFromPayload(listPayload);

  return (
    <ProtectedPage
      title="Reconciliation snapshots"
      description="Admin dashboard для snapshot history, repair impact, compare и retention."
    >
      {!isAdmin ? (
        <div className="container page">
          <div className="card error">У текущей сессии нет admin-role.</div>
        </div>
      ) : (
        <div className="container page">
          <div className="section row" style={{ alignItems: 'flex-start' }}>
            <div>
              <span className="badge secondary">Reconciliation dashboard</span>
              <h1>Reconciliation snapshots</h1>
              <p className="lead">
                Единая админская панель для v8.30-v8.34: auto-capture после repair, trend, compare, scheduled capture и retention.
              </p>
              <p className="muted">
                Latest: {latestSnapshot ? `${sourceTitle(latestSnapshot.source)} · ${formatDate(latestSnapshot.generated_at)}` : 'snapshot history empty'}
              </p>
            </div>
            <div className="inline">
              <Link className="btn secondary" href="/admin/reconciliation">Live report</Link>
              <Link className="btn secondary" href="/admin/operations">Operations</Link>
              <button className="btn secondary" type="button" disabled={isLoading || isCapturing} onClick={() => void load()}>
                {isLoading ? 'Loading...' : 'Refresh'}
              </button>
              <button className="btn" type="button" disabled={isCapturing || isLoading} onClick={() => void capture()}>
                {isCapturing ? 'Capturing...' : 'Capture snapshot'}
              </button>
            </div>
          </div>

          {msg ? <div className="card warning section">{msg}</div> : null}

          <div className="section card compact">
            <div className="form-row">
              <label className="form-group">
                <span className="label">Limit</span>
                <select className="select" value={limit} onChange={(event) => setLimit(Number(event.target.value))}>
                  {[10, 20, 30, 50, 100, 250].map((value) => (
                    <option key={value} value={value}>{value}</option>
                  ))}
                </select>
              </label>
              <label className="form-group">
                <span className="label">Source</span>
                <select className="select" value={source} onChange={(event) => setSource(event.target.value)}>
                  {SOURCE_FILTERS.map((value) => (
                    <option key={value || 'any-source'} value={value}>{value ? sourceTitle(value) : 'Any source'}</option>
                  ))}
                </select>
              </label>
              <label className="form-group">
                <span className="label">Status</span>
                <select className="select" value={status} onChange={(event) => setStatus(event.target.value)}>
                  {STATUS_FILTERS.map((value) => (
                    <option key={value || 'any-status'} value={value}>{value ? statusTitle(value) : 'Any status'}</option>
                  ))}
                </select>
              </label>
              <div className="form-group">
                <span className="label">Apply</span>
                <button className="btn secondary" type="button" disabled={isLoading} onClick={() => void load()}>
                  Apply filters
                </button>
              </div>
            </div>
          </div>

          {!listPayload && !msg ? <div className="empty-state section">Загрузка reconciliation dashboard...</div> : null}

          {listPayload ? (
            <>
              <section className="section">
                <ReconciliationHealthCard latestSnapshot={latestSnapshot} metrics={metrics} schedule={schedule} />
              </section>

              <section className="section grid-2">
                <ReconciliationSnapshotTrend trend={trend} metrics={metrics} />
                <ReconciliationRepairImpact metrics={metrics} repairSnapshots={repairSnapshots} />
              </section>

              <section className="section">
                <ReconciliationComparePanel snapshots={snapshots} />
              </section>

              <section className="section grid-2">
                <ReconciliationRetentionPanel initialPreview={retentionPreview} onChanged={() => void load()} />
                <SnapshotHistoryPanel snapshots={snapshots} />
              </section>
            </>
          ) : null}
        </div>
      )}
    </ProtectedPage>
  );
}
