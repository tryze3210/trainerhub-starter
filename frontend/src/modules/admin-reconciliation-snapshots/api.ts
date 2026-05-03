import { apiRequest } from '@/lib/api-client';

export type SnapshotStatus = 'ok' | 'degraded' | 'critical' | 'missing' | string;
export type SnapshotSource = 'manual' | 'scheduled' | 'repair' | 'ci' | string;
export type DeltaDirection = 'baseline' | 'improved' | 'worsened' | 'unchanged' | string;

export type SnapshotDelta = {
  has_previous: boolean;
  previous_snapshot_id?: string | null;
  previous_generated_at?: string | null;
  total_issues_delta: number;
  critical_count_delta: number;
  warning_count_delta: number;
  direction: DeltaDirection;
};

export type SnapshotSectionStatus = {
  status: SnapshotStatus;
  issue_count: number;
  critical_count: number;
  warning_count: number;
};

export type ReconciliationSnapshot = {
  id: string;
  href?: string;
  status: SnapshotStatus;
  source: SnapshotSource;
  generated_at: string;
  created_at?: string;
  created_by?: string | null;
  correlation_id?: string;
  summary?: Record<string, unknown>;
  section_statuses?: Record<string, SnapshotSectionStatus | undefined>;
  total_issues: number;
  critical_count: number;
  warning_count: number;
  info_count: number;
  delta?: SnapshotDelta;
  report?: Record<string, unknown>;
  audit_event_id?: string;
  audit_event_href?: string;
};

export type SnapshotSummary = {
  latest_snapshot_id?: string | null;
  latest_status: SnapshotStatus;
  latest_generated_at?: string | null;
  latest_total_issues: number;
  latest_critical_count: number;
  snapshot_count: number;
  by_status?: Array<{ status: SnapshotStatus; count: number }>;
  by_source?: Array<{ source: SnapshotSource; count: number }>;
};

export type SnapshotListResponse = {
  status: SnapshotStatus;
  generated_at: string;
  count: number;
  filters: {
    limit: number;
    source?: string;
    status?: string;
    include_report?: boolean;
  };
  summary: SnapshotSummary;
  snapshots: ReconciliationSnapshot[];
};

export type SnapshotTrendPoint = {
  id: string;
  status: SnapshotStatus;
  source: SnapshotSource;
  generated_at: string;
  total_issues: number;
  critical_count: number;
  warning_count: number;
  info_count: number;
};

export type SnapshotTrendResponse = {
  status: SnapshotStatus;
  generated_at: string;
  summary: SnapshotSummary;
  delta?: SnapshotDelta;
  points: SnapshotTrendPoint[];
};

export type SnapshotListParams = {
  limit?: number;
  source?: string;
  status?: string;
  include_report?: boolean;
};

export type SnapshotCapturePayload = {
  limit?: number;
  source?: 'manual' | 'scheduled' | 'repair' | 'ci';
  correlation_id?: string;
};

function buildQuery(params?: Record<string, string | number | boolean | undefined | null>) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params || {})) {
    if (value === undefined || value === null || value === '') continue;
    query.set(key, String(value));
  }
  const value = query.toString();
  return value ? `?${value}` : '';
}

export const adminReconciliationSnapshotsApi = {
  list: (params?: SnapshotListParams) =>
    apiRequest<SnapshotListResponse>(`/ops/admin/reconciliation-snapshots/${buildQuery(params)}`, {
      auth: true,
    }),

  trend: (params?: { limit?: number }) =>
    apiRequest<SnapshotTrendResponse>(`/ops/admin/reconciliation-snapshots/trend/${buildQuery(params)}`, {
      auth: true,
    }),

  capture: (payload: SnapshotCapturePayload) =>
    apiRequest<ReconciliationSnapshot>('/ops/admin/reconciliation-snapshots/capture/', {
      method: 'POST',
      auth: true,
      body: JSON.stringify(payload),
    }),
};
