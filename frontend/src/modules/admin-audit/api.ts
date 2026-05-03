import { apiRequest, normalizeListResponse } from '@/lib/api-client';

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
  limit?: number;
};

function buildQuery(params?: AuditEventFilters) {
  const search = new URLSearchParams();
  if (params?.event_type) search.set('event_type', params.event_type);
  if (params?.entity_type) search.set('entity_type', params.entity_type);
  if (params?.entity_id) search.set('entity_id', params.entity_id);
  if (params?.actor_id) search.set('actor_id', params.actor_id);
  if (params?.limit) search.set('limit', String(params.limit));
  const query = search.toString();
  return query ? `?${query}` : '';
}

export const adminAuditApi = {
  async listEvents(params?: AuditEventFilters): Promise<AuditEvent[]> {
    const payload = await apiRequest<AuditEvent[] | { results: AuditEvent[] }>(
      `/audit/admin/events/${buildQuery(params)}`,
      { auth: true }
    );
    return normalizeListResponse(payload);
  },
};
