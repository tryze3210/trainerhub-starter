import { apiRequest } from '@/lib/api-client';

export type JsonRecord = Record<string, unknown>;

export type SnapshotStatus = 'ok' | 'degraded' | 'critical' | 'missing' | 'failed' | string;
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
  status?: SnapshotStatus;
  issue_count?: number;
  critical_count?: number;
  warning_count?: number;
  info_count?: number;
  total_issues?: number;
  [key: string]: unknown;
};

export type ReconciliationSnapshot = {
  id: string;
  href?: string;
  status: SnapshotStatus;
  source: SnapshotSource;
  generated_at: string;
  created_at?: string;
  created_by?: string | null;
  correlation_id?: string | null;
  summary?: JsonRecord;
  section_statuses?: Record<string, SnapshotSectionStatus>;
  total_issues: number;
  critical_count: number;
  warning_count: number;
  info_count: number;
  delta?: SnapshotDelta;
  report?: JsonRecord;
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
  filters: { limit: number; source?: string; status?: string; include_report?: boolean };
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

export type SnapshotLatestResponse = {
  status?: SnapshotStatus;
  generated_at?: string;
  source?: SnapshotSource;
  snapshot?: ReconciliationSnapshot | null;
  latest?: ReconciliationSnapshot | null;
  message?: string;
};

export type SnapshotCompareIssue = {
  key?: string;
  code?: string;
  section?: string;
  severity?: string;
  entity_type?: string;
  entity_id?: string;
  message?: string;
  previous_severity?: string;
  current_severity?: string;
  [key: string]: unknown;
};

export type SnapshotCompareResponse = {
  status: SnapshotStatus;
  generated_at?: string;
  baseline?: ReconciliationSnapshot | null;
  current?: ReconciliationSnapshot | null;
  baseline_snapshot?: ReconciliationSnapshot | null;
  current_snapshot?: ReconciliationSnapshot | null;
  summary?: {
    baseline_total_issues?: number;
    current_total_issues?: number;
    total_issues_delta?: number;
    resolved_count?: number;
    added_count?: number;
    persisted_count?: number;
    severity_changed_count?: number;
    direction?: DeltaDirection;
    [key: string]: unknown;
  };
  resolved?: SnapshotCompareIssue[];
  added?: SnapshotCompareIssue[];
  persisted?: SnapshotCompareIssue[];
  severity_changed?: SnapshotCompareIssue[];
  sections?: Record<string, JsonRecord>;
  section_deltas?: Record<string, JsonRecord>;
};

export type SnapshotMetricsResponse = {
  status?: SnapshotStatus;
  generated_at?: string;
  headline?: {
    latest_snapshot_id?: string | null;
    latest_status?: SnapshotStatus;
    latest_generated_at?: string | null;
    latest_total_issues?: number;
    latest_critical_count?: number;
    previous_snapshot_id?: string | null;
    previous_total_issues?: number;
    previous_critical_count?: number;
    total_issues_delta?: number;
    critical_count_delta?: number;
    direction?: DeltaDirection;
    [key: string]: unknown;
  };
  distribution?: {
    by_status?: Array<{ status: SnapshotStatus; count: number }>;
    by_source?: Array<{ source: SnapshotSource; count: number }>;
    [key: string]: unknown;
  };
  section_metrics?: Record<string, JsonRecord> | Array<JsonRecord>;
  repair_effectiveness?: {
    total?: number;
    improved?: number;
    worsened?: number;
    unchanged?: number;
    failed?: number;
    [key: string]: unknown;
  };
  trend?: {
    points?: SnapshotTrendPoint[];
    [key: string]: unknown;
  };
  [key: string]: unknown;
};

export type SnapshotScheduleResponse = {
  status?: SnapshotStatus;
  generated_at?: string;
  source?: SnapshotSource;
  min_age_minutes?: number;
  latest_snapshot?: ReconciliationSnapshot | null;
  latest_generated_at?: string | null;
  due?: boolean;
  next_capture_due_at?: string | null;
  message?: string;
  [key: string]: unknown;
};

export type SnapshotRetentionResponse = {
  status?: SnapshotStatus;
  generated_at?: string;
  dry_run?: boolean;
  deleted_count?: number;
  candidate_count?: number;
  protected_count?: number;
  candidates?: ReconciliationSnapshot[];
  protected_snapshots?: ReconciliationSnapshot[];
  protected?: ReconciliationSnapshot[];
  policy?: JsonRecord;
  summary?: JsonRecord;
  [key: string]: unknown;
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

export type SnapshotCompareParams = {
  baseline_id?: string;
  current_id?: string;
  source?: string;
};

export type SnapshotMetricsParams = {
  limit?: number;
  source?: string;
  status?: string;
};

export type SnapshotRetentionPayload = {
  dry_run?: boolean;
  source?: string;
  keep_min_per_source?: number;
  scheduled_days?: number;
  repair_days?: number;
  manual_days?: number;
  ci_days?: number;
};

function buildQuery(params?: Record<string, unknown>) {
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

  latest: (params?: { source?: string; status?: string }) =>
    apiRequest<SnapshotLatestResponse>(`/ops/admin/reconciliation-snapshots/latest/${buildQuery(params)}`, {
      auth: true,
    }),

  compare: (params?: SnapshotCompareParams) =>
    apiRequest<SnapshotCompareResponse>(`/ops/admin/reconciliation-snapshots/compare/${buildQuery(params)}`, {
      auth: true,
    }),

  metrics: (params?: SnapshotMetricsParams) =>
    apiRequest<SnapshotMetricsResponse>(`/ops/admin/reconciliation-snapshots/metrics/${buildQuery(params)}`, {
      auth: true,
    }),

  schedule: (params?: { source?: string; min_age_minutes?: number }) =>
    apiRequest<SnapshotScheduleResponse>(`/ops/admin/reconciliation-snapshots/schedule/${buildQuery(params)}`, {
      auth: true,
    }),

  retention: (params?: SnapshotRetentionPayload) =>
    apiRequest<SnapshotRetentionResponse>(`/ops/admin/reconciliation-snapshots/retention/${buildQuery(params)}`, {
      auth: true,
    }),

  pruneRetention: (payload: SnapshotRetentionPayload) =>
    apiRequest<SnapshotRetentionResponse>('/ops/admin/reconciliation-snapshots/retention/', {
      method: 'POST',
      auth: true,
      body: JSON.stringify(payload),
    }),

  capture: (payload: SnapshotCapturePayload) =>
    apiRequest<ReconciliationSnapshot>('/ops/admin/reconciliation-snapshots/capture/', {
      method: 'POST',
      auth: true,
      body: JSON.stringify(payload),
    }),
};
