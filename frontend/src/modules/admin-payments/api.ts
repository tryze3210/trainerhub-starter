import { apiRequest, normalizeListResponse, type PaginatedResponse } from '@/lib/api-client';

export type AdminPaymentStatus =
  | 'created'
  | 'pending'
  | 'succeeded'
  | 'failed'
  | 'cancelled'
  | 'refunded'
  | 'disputed'
  | 'charged_back'
  | string;

export type AdminPaymentEntitlementSummary = {
  status: 'active' | 'revoked' | 'expired' | 'missing' | 'not_granted' | string;
  total: number;
  active: number;
  revoked: number;
  expired: number;
};

export type AdminPaymentRefundOperation = {
  refund_id?: string;
  amount?: string | number;
  reason?: string;
  status?: string;
  type?: string;
  requested_at?: string | null;
  completed_at?: string | null;
  created_at?: string | null;
  [key: string]: unknown;
};

export type AdminPayment = {
  id: string;
  order_id: string;
  provider: string;
  status: AdminPaymentStatus;
  amount: string;
  currency: string;
  external_payment_id?: string;
  external_checkout_url?: string;
  provider_payload?: Record<string, unknown>;
  confirmed_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  buyer_id?: string;
  buyer_email?: string;
  order_status?: string;
  order_type?: string;
  order_total_amount?: string;
  refund_operations?: AdminPaymentRefundOperation[];
  entitlement_summary?: AdminPaymentEntitlementSummary;
};

export type AdminPaymentWebhookEvent = {
  id: string;
  provider: string;
  event_type: string;
  external_event_id: string;
  payment_id?: string | null;
  status: string;
  payload?: Record<string, unknown>;
  headers?: Record<string, unknown>;
  signature?: string;
  raw_payload_hash?: string;
  error_message?: string;
  attempts: number;
  received_at?: string | null;
  processed_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type PaymentReconciliationIssue = {
  code: string;
  severity: string;
  entity_type: string;
  entity_id: string;
  message: string;
  suggested_action: string;
  related?: Array<{ entity_type: string; entity_id: string; label?: string; href?: string }>;
  evidence?: Record<string, unknown>;
};

export type PaymentReconciliationReport = {
  status: 'ok' | 'degraded' | 'critical' | string;
  generated_at: string;
  summary: {
    total_issues: number;
    critical_count: number;
    warning_count: number;
    by_severity?: Record<string, number>;
  };
  metrics: Record<string, Record<string, unknown> | unknown>;
  checks: Array<{ code: string; description?: string }>;
  issues: PaymentReconciliationIssue[];
};

export type AdminPaymentFilters = {
  status?: string;
  provider?: string;
  buyer_email?: string;
  external_payment_id?: string;
  order_id?: string;
  limit?: number;
};

export type AdminWebhookFilters = {
  provider?: string;
  status?: string;
  event_type?: string;
  external_payment_id?: string;
  limit?: number;
};

function buildQuery(params?: Record<string, string | number | boolean | null | undefined>) {
  const query = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, String(value));
    }
  });
  const value = query.toString();
  return value ? `?${value}` : '';
}

function listFromPayload<T>(payload: T[] | PaginatedResponse<T> | { results?: T[] } | null | undefined): T[] {
  if (!payload) return [];
  if (Array.isArray(payload)) return payload;
  if ('results' in payload && Array.isArray(payload.results)) return payload.results;
  return normalizeListResponse(payload as T[] | PaginatedResponse<T> | null | undefined);
}

export const adminPaymentsApi = {
  async listPayments(params?: AdminPaymentFilters) {
    const payload = await apiRequest<AdminPayment[] | PaginatedResponse<AdminPayment> | { results: AdminPayment[] }>(
      `/payments-admin/${buildQuery(params)}`,
      { auth: true }
    );
    return listFromPayload(payload);
  },

  async listWebhookEvents(params?: AdminWebhookFilters) {
    const payload = await apiRequest<
      AdminPaymentWebhookEvent[] | PaginatedResponse<AdminPaymentWebhookEvent> | { results: AdminPaymentWebhookEvent[] }
    >(`/payments-webhooks/${buildQuery(params)}`, { auth: true });
    return listFromPayload(payload);
  },

  async reprocessWebhook(eventId: string, force = false) {
    return apiRequest<{ webhook_event_id: string; status: string; processed_at?: string | null; event?: AdminPaymentWebhookEvent }>(
      `/payments-webhooks/${eventId}/reprocess/`,
      {
        method: 'POST',
        auth: true,
        body: JSON.stringify({ force }),
      }
    );
  },

  async getPaymentReconciliation(limit = 100) {
    return apiRequest<PaymentReconciliationReport>(`/ops/admin/payment-reconciliation/?limit=${limit}`, {
      auth: true,
    });
  },
};
