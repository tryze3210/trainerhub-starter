import { apiRequest, normalizeListResponse, type PaginatedResponse } from '@/lib/api-client';

export type AdminPayoutStatus = 'pending' | 'requested' | 'approved' | 'processing' | 'paid' | 'rejected' | string;

export type AdminPayoutRequest = {
  id: string;
  trainer_id?: string;
  wallet_id?: string;
  amount: string;
  currency: string;
  status: AdminPayoutStatus;
  destination_masked?: string;
  requested_at?: string | null;
  approved_at?: string | null;
  processed_at?: string | null;
  rejected_reason?: string;
  metadata?: Record<string, unknown>;
  ledger_entries?: AdminPayoutLedgerEntry[];
  created_at?: string | null;
  updated_at?: string | null;
};

export type AdminPayoutLedgerEntry = {
  id: string;
  payout_request?: string | null;
  payment_id?: string | null;
  entry_type: string;
  amount: string;
  currency: string;
  metadata?: Record<string, unknown>;
  created_at?: string | null;
  updated_at?: string | null;
};

export type AdminPayoutStatusBucket = {
  status: string;
  count: number;
  amount: string;
};

export type AdminPayoutLedgerBucket = {
  entry_type: string;
  count: number;
  amount: string;
};

export type AdminPayoutBalanceTotals = {
  available_amount: string;
  reserved_amount: string;
  lifetime_earned_amount: string;
  trainers_count: number;
};

export type AdminPayoutOpsSummary = {
  pending_exposure_amount: string;
  pending_exposure_count: number;
  reserved_amount: string;
  available_amount: string;
  reconciliation_status?: string;
  reconciliation_issue_count?: number;
};

export type AdminPayoutOverview = {
  statuses: AdminPayoutStatusBucket[];
  ledger: AdminPayoutLedgerBucket[];
  balances: AdminPayoutBalanceTotals;
  ops: AdminPayoutOpsSummary;
  recent_requests: AdminPayoutRequest[];
};

export type PayoutReconciliationIssue = {
  code: string;
  severity: string;
  trainer_id?: string;
  currency?: string;
  available_amount?: string;
  reserved_amount?: string;
  active_payout_amount?: string;
  active_payout_count?: number;
  delta?: string;
  message?: string;
};

export type PayoutReconciliationReport = {
  status: 'healthy' | 'attention_required' | string;
  checked_at?: string;
  issue_count: number;
  issues: PayoutReconciliationIssue[];
};

export type AdminPayoutRiskHold = {
  id: string;
  payment_id?: string;
  trainer_id?: string;
  wallet_id?: string;
  amount: string;
  currency: string;
  status: string;
  source_type?: string;
  released_amount?: string;
  consumed_amount?: string;
  active_amount?: string;
  created_at?: string | null;
  updated_at?: string | null;
};

export type AdminPayoutRiskHoldSummary = {
  status: string;
  active_hold_count: number;
  active_hold_amount: string;
  released_hold_count: number;
  consumed_hold_count: number;
  shortfall_count: number;
  recent_holds: AdminPayoutRiskHold[];
};

export type AdminPayoutProjectionHealth = {
  consumer: string;
  status: string;
  projected_messages: number;
  skipped_messages: number;
  failed_messages: number;
  latest_processed_at?: string | null;
  latest_message_key?: string;
  latest_payload?: Record<string, unknown>;
  ledger_accrual_amount?: string;
  ledger_counts?: Array<{ entry_type: string; currency: string; count: number; amount: string }>;
};

export type AdminPayoutTransitionPayload = {
  action?: 'approve' | 'processing' | 'paid' | 'reject';
  reason?: string;
  external_reference?: string;
};

export type AdminPayoutBulkTransitionPayload = AdminPayoutTransitionPayload & {
  action: 'approve' | 'processing' | 'paid' | 'reject';
  payout_ids: string[];
};

export type AdminPayoutBulkTransitionResult = {
  results: Array<{ id: string; ok: boolean; status?: string; error?: unknown }>;
};

function listFromPayload<T>(payload: T[] | PaginatedResponse<T> | { results?: T[] } | null | undefined): T[] {
  if (!payload) return [];
  if (Array.isArray(payload)) return payload;
  if ('results' in payload && Array.isArray(payload.results)) return payload.results;
  return normalizeListResponse(payload as T[] | PaginatedResponse<T> | null | undefined);
}

export const adminPayoutsApi = {
  async getOverview() {
    return apiRequest<AdminPayoutOverview>('/payouts/admin/overview/', { auth: true });
  },

  async listPayouts(params?: { status?: string; trainer_id?: string; limit?: number }) {
    const search = new URLSearchParams();
    if (params?.status) search.set('status', params.status);
    if (params?.trainer_id) search.set('trainer_id', params.trainer_id);
    if (params?.limit) search.set('limit', String(params.limit));
    const suffix = search.toString() ? `?${search.toString()}` : '';
    const payload = await apiRequest<AdminPayoutRequest[] | PaginatedResponse<AdminPayoutRequest> | { results: AdminPayoutRequest[] }>(`/payouts/admin/${suffix}`, { auth: true });
    return listFromPayload(payload);
  },

  async getPayout(payoutId: string) {
    return apiRequest<AdminPayoutRequest>(`/payouts/admin/${payoutId}/`, { auth: true });
  },

  async transition(payoutId: string, payload: AdminPayoutTransitionPayload & { action: 'approve' | 'processing' | 'paid' | 'reject' }) {
    return apiRequest<AdminPayoutRequest>(`/payouts/admin/${payoutId}/transition/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async approve(payoutId: string, payload: Pick<AdminPayoutTransitionPayload, 'external_reference'> = {}) {
    return apiRequest<AdminPayoutRequest>(`/payouts/admin/${payoutId}/approve/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async markProcessing(payoutId: string, payload: Pick<AdminPayoutTransitionPayload, 'external_reference'> = {}) {
    return apiRequest<AdminPayoutRequest>(`/payouts/admin/${payoutId}/processing/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async markPaid(payoutId: string, payload: Pick<AdminPayoutTransitionPayload, 'external_reference'> = {}) {
    return apiRequest<AdminPayoutRequest>(`/payouts/admin/${payoutId}/mark-paid/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async reject(payoutId: string, payload: Required<Pick<AdminPayoutTransitionPayload, 'reason'>> & Pick<AdminPayoutTransitionPayload, 'external_reference'>) {
    return apiRequest<AdminPayoutRequest>(`/payouts/admin/${payoutId}/reject/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async bulkTransition(payload: AdminPayoutBulkTransitionPayload) {
    return apiRequest<AdminPayoutBulkTransitionResult>('/payouts/admin/bulk-transition/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getProjectionHealth() {
    return apiRequest<AdminPayoutProjectionHealth>('/payouts/admin/projection-health/', { auth: true });
  },

  async projectOutbox(batchSize = 100) {
    return apiRequest<Record<string, unknown>>('/payouts/admin/project-outbox/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify({ batch_size: batchSize }),
    });
  },

  async getReconciliation() {
    return apiRequest<PayoutReconciliationReport>('/payouts/admin/reconciliation/', { auth: true });
  },

  async repairReconciliation(dryRun = true) {
    return apiRequest<Record<string, unknown>>('/payouts/admin/reconciliation/repair/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify({ dry_run: dryRun }),
    });
  },

  async listRiskHolds(params?: { status?: string; trainer_id?: string; payment_id?: string; limit?: number }) {
    const search = new URLSearchParams();
    if (params?.status) search.set('status', params.status);
    if (params?.trainer_id) search.set('trainer_id', params.trainer_id);
    if (params?.payment_id) search.set('payment_id', params.payment_id);
    if (params?.limit) search.set('limit', String(params.limit));
    const suffix = search.toString() ? `?${search.toString()}` : '';
    const payload = await apiRequest<AdminPayoutRiskHold[] | PaginatedResponse<AdminPayoutRiskHold> | { results: AdminPayoutRiskHold[] }>(`/payouts/admin/risk-holds/${suffix}`, { auth: true });
    return listFromPayload(payload);
  },

  async getRiskHoldSummary(limit = 50) {
    return apiRequest<AdminPayoutRiskHoldSummary>(`/payouts/admin/risk-holds/summary/?limit=${limit}`, { auth: true });
  },

  async releaseRiskHold(paymentId: string, reason = 'manual_admin_release') {
    return apiRequest<Record<string, unknown>>('/payouts/admin/risk-holds/release/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify({ payment_id: paymentId, reason }),
    });
  },
};
