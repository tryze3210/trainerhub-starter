import { apiRequest } from '@/lib/api-client';

export type AdminEntityRelationship = {
  entity_type: string;
  entity_id: string;
  label: string;
  href: string;
};

export type AdminEntityDetail = {
  entity_type: string;
  entity_id: string;
  title: string;
  status: string;
  primary: Record<string, unknown>;
  payload: Record<string, unknown>;
  relationships: AdminEntityRelationship[];
  raw: Record<string, unknown>;
};

export type AdminEntityActionResult = {
  status?: string;
  detail?: string;
  id?: string;
  processed_at?: string | null;
  attempts?: number;
  released_amount?: string;
  payment_id?: string;
  [key: string]: unknown;
};

export function adminEntityHref(entityType?: string | null, entityId?: string | null) {
  if (!entityType || !entityId) return '';
  return `/admin/entities/${encodeURIComponent(String(entityType))}/${encodeURIComponent(String(entityId))}`;
}

export const adminEntityDetailsApi = {
  getDetail: (entityType: string, entityId: string) =>
    apiRequest<AdminEntityDetail>(
      `/ops/admin/entities/${encodeURIComponent(entityType)}/${encodeURIComponent(entityId)}/`,
      { auth: true }
    ),

  retryOutboxMessage: (messageId: string, payload: { force?: boolean; reset_attempts?: boolean } = {}) =>
    apiRequest<AdminEntityActionResult>(`/events/outbox/${encodeURIComponent(messageId)}/retry/`, {
      method: 'POST',
      auth: true,
      body: JSON.stringify({
        force: payload.force ?? true,
        reset_attempts: payload.reset_attempts ?? true,
      }),
    }),

  markOutboxDead: (messageId: string, reason: string) =>
    apiRequest<AdminEntityActionResult>(`/events/outbox/${encodeURIComponent(messageId)}/dead/`, {
      method: 'POST',
      auth: true,
      body: JSON.stringify({ reason }),
    }),

  reprocessPaymentWebhook: (webhookId: string, force = false) =>
    apiRequest<AdminEntityActionResult>(`/payments-webhooks/${encodeURIComponent(webhookId)}/reprocess/`, {
      method: 'POST',
      auth: true,
      body: JSON.stringify({ force }),
    }),

  releaseRiskHold: (paymentId: string, reason = 'manual_ops_release_from_admin_entity_detail') =>
    apiRequest<AdminEntityActionResult>('/payouts/admin/risk-holds/release/', {
      method: 'POST',
      auth: true,
      body: JSON.stringify({ payment_id: paymentId, reason }),
    }),
};
