import { apiRequest, normalizeListResponse, type PaginatedResponse } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';
import { API_BASE_URL } from '@/lib/config';

export type AuditRequestContext = {
  method?: string;
  path?: string;
  correlation_id?: string;
};

export type AuditEventContext = {
  action?: string;
  target_type?: string;
  target_id?: string;
  reason?: string;
  status?: string;
  request?: AuditRequestContext;
  context?: Record<string, unknown>;
  result?: Record<string, unknown> | unknown;
  input?: Record<string, unknown> | unknown;
  recorded_at?: string;
  [key: string]: unknown;
};

export type AuditEvent = {
  id: string;
  actor?: string | null;
  actor_email?: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  context?: AuditEventContext | null;
  ip_address?: string | null;
  user_agent?: string;
  created_at: string;
  updated_at?: string;
};

export type AuditEventFilters = {
  event_type?: string;
  entity_type?: string;
  entity_id?: string;
  actor_id?: string;
  created_from?: string;
  created_to?: string;
  search?: string;
  limit?: number;
};

export type AuditRetentionFilters = Omit<AuditEventFilters, 'limit'> & {
  older_than_days?: number;
};

export type AuditRetentionEventTypeBucket = {
  event_type: string | null;
  count: number;
};

export type AuditRetentionEntityTypeBucket = {
  entity_type: string | null;
  count: number;
};

export type AuditRetentionSummary = {
  older_than_days: number;
  cutoff: string;
  total_matching_events: number;
  stale_events: number;
  oldest_created_at: string | null;
  newest_created_at: string | null;
  filters: Record<string, string>;
  by_event_type: AuditRetentionEventTypeBucket[];
  by_entity_type: AuditRetentionEntityTypeBucket[];
  note: string;
};

type AuditEventListPayload = AuditEvent[] | PaginatedResponse<AuditEvent> | null | undefined;

type AuditQueryParams = AuditEventFilters | AuditRetentionFilters;

function buildQuery(params?: AuditQueryParams) {
  const search = new URLSearchParams();

  if (params?.event_type) search.set('event_type', params.event_type);
  if (params?.entity_type) search.set('entity_type', params.entity_type);
  if (params?.entity_id) search.set('entity_id', params.entity_id);
  if (params?.actor_id) search.set('actor_id', params.actor_id);
  if (params?.created_from) search.set('created_from', params.created_from);
  if (params?.created_to) search.set('created_to', params.created_to);
  if (params?.search) search.set('search', params.search);

  const limit = params && 'limit' in params ? params.limit : undefined;
  if (limit) search.set('limit', String(limit));

  const olderThanDays = params && 'older_than_days' in params ? params.older_than_days : undefined;
  if (olderThanDays) search.set('older_than_days', String(olderThanDays));

  const query = search.toString();
  return query ? `?${query}` : '';
}

function withApiBase(path: string): string {
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }

  return `${API_BASE_URL}${path}`;
}

function filenameFromContentDisposition(value: string | null, fallback: string): string {
  if (!value) return fallback;

  const utf8Match = value.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) {
    try {
      return decodeURIComponent(utf8Match[1].replace(/"/g, '').trim());
    } catch {
      return utf8Match[1].replace(/"/g, '').trim() || fallback;
    }
  }

  const asciiMatch = value.match(/filename="?([^";]+)"?/i);
  return asciiMatch?.[1]?.trim() || fallback;
}

function defaultAuditExportFilename(): string {
  const date = new Date().toISOString().slice(0, 10);
  return `trainerhub-admin-audit-events-${date}.csv`;
}

export function buildAdminAuditExportPath(params?: AuditEventFilters): string {
  return `/audit/admin/events/export.csv${buildQuery(params)}`;
}

export function buildAdminAuditRetentionSummaryPath(params?: AuditRetentionFilters): string {
  return `/audit/admin/retention/summary/${buildQuery(params)}`;
}

export async function downloadAdminAuditCsv(params?: AuditEventFilters): Promise<string> {
  if (typeof window === 'undefined' || typeof document === 'undefined') {
    throw new Error('CSV export is available only in browser session');
  }

  const token = getAccessToken();
  const response = await fetch(withApiBase(buildAdminAuditExportPath(params)), {
    method: 'GET',
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    cache: 'no-store',
    credentials: 'include',
  });

  if (!response.ok) {
    const message = await response.text().catch(() => '');
    throw new Error(message || `Audit CSV export failed: HTTP ${response.status}`);
  }

  const blob = await response.blob();
  const filename = filenameFromContentDisposition(
    response.headers.get('Content-Disposition'),
    defaultAuditExportFilename()
  );

  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.rel = 'noopener';
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(url);

  return filename;
}

export const adminAuditApi = {
  async listEvents(params?: AuditEventFilters): Promise<AuditEvent[]> {
    const payload = await apiRequest<AuditEventListPayload>(
      `/audit/admin/events/${buildQuery(params)}`,
      { auth: true }
    );

    return normalizeListResponse<AuditEvent>(payload);
  },

  async getRetentionSummary(params?: AuditRetentionFilters): Promise<AuditRetentionSummary> {
    return apiRequest<AuditRetentionSummary>(buildAdminAuditRetentionSummaryPath(params), { auth: true });
  },
};
