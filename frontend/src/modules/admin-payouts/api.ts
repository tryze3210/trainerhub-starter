import { apiRequest, normalizeListResponse, type PaginatedResponse } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';
import { API_BASE_URL } from '@/lib/config';

export type AdminPayoutStatus =
  | 'pending'
  | 'requested'
  | 'approved'
  | 'processing'
  | 'paid'
  | 'rejected'
  | string;

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
  trainer_id?: string | null;
  wallet_id?: string | null;
  entry_type: string;
  direction?: string;
  status?: string;
  source_type?: string;
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
  status?: string;
  direction?: string;
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

export type PayoutAdminOpsFilters = {
  status?: string;
  trainer_id?: string;
  currency?: string;
  created_from?: string;
  created_to?: string;
  limit?: number;
};

export type PayoutAdminOpsLedgerFilters = PayoutAdminOpsFilters & {
  entry_type?: string;
  direction?: string;
  source_type?: string;
};

export type PayoutAdminOpsBucket = {
  status?: string;
  entry_type?: string;
  direction?: string;
  source_type?: string;
  currency?: string;
  count: number;
  amount: string;
};

export type PayoutWalletTotals = {
  available_amount?: string;
  pending_amount?: string;
  locked_amount?: string;
  reserved_amount?: string;
  lifetime_earned_amount?: string;
  trainers_count?: number;
};

export type PayoutAdminOpsSummaryResponse = {
  generated_at?: string;
  filters?: Record<string, string | number | null | undefined>;
  summary: {
    total_payout_requests: number;
    total_payout_amount?: string;
    active_payout_count: number;
    active_payout_amount: string;
    paid_payout_count?: number;
    paid_payout_amount?: string;
  };
  wallet_totals?: PayoutWalletTotals;
  payout_buckets?: PayoutAdminOpsBucket[];
  status_buckets?: PayoutAdminOpsBucket[];
  ledger_buckets?: PayoutAdminOpsBucket[];
  recent_payout_requests?: AdminPayoutRequest[];
  recent_requests?: AdminPayoutRequest[];
  reconciliation?: {
    status?: string;
    issue_count?: number;
    checked_at?: string | null;
  };
};

export type PayoutAdminOpsReconciliationSnapshot = {
  generated_at?: string;
  mode?: string;
  summary?: {
    status?: string;
    issue_count?: number;
    checked_at?: string | null;
  };
  snapshot?: PayoutReconciliationReport | Record<string, unknown>;
  actions?: {
    repair_performed?: boolean;
  };
};

function listFromPayload<T>(payload: T[] | PaginatedResponse<T> | { results?: T[] } | null | undefined): T[] {
  if (!payload) return [];
  if (Array.isArray(payload)) return payload;
  if ('results' in payload && Array.isArray(payload.results)) return payload.results;
  return normalizeListResponse(payload as T[] | PaginatedResponse<T> | null | undefined);
}

function buildQuery(params?: Record<string, string | number | boolean | null | undefined>) {
  const search = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, String(value));
    }
  });
  const query = search.toString();
  return query ? `?${query}` : '';
}

function filenameFromDisposition(disposition: string | null, fallback: string) {
  if (!disposition) return fallback;
  const match = disposition.match(/filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i);
  const raw = match?.[1] || match?.[2];
  return raw ? decodeURIComponent(raw) : fallback;
}

async function downloadCsv(path: string, fallbackFilename: string) {
  const headers = new Headers();
  const token = getAccessToken();
  if (token) headers.set('Authorization', `Bearer ${token}`);

  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers,
    cache: 'no-store',
  });

  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) message = payload.detail;
    } catch {
      // Keep HTTP status fallback for non-JSON errors.
    }
    throw new Error(message);
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filenameFromDisposition(response.headers.get('Content-Disposition'), fallbackFilename);
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(url);
}

export const adminPayoutsApi = {
  async getOverview() {
    return apiRequest<AdminPayoutOverview>('/payouts/admin/overview/', { auth: true });
  },

  async listPayouts(params?: { status?: string; trainer_id?: string; limit?: number }) {
    const payload = await apiRequest<AdminPayoutRequest[] | PaginatedResponse<AdminPayoutRequest> | { results: AdminPayoutRequest[] }>(
      `/payouts/admin/${buildQuery(params)}`,
      { auth: true }
    );
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
    const payload = await apiRequest<AdminPayoutRiskHold[] | PaginatedResponse<AdminPayoutRiskHold> | { results: AdminPayoutRiskHold[] }>(
      `/payouts/admin/risk-holds/${buildQuery(params)}`,
      { auth: true }
    );
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

  async getAdminOpsSummary(params?: PayoutAdminOpsFilters) {
    return apiRequest<PayoutAdminOpsSummaryResponse>(`/payouts/admin-ops/summary/${buildQuery(params)}`, { auth: true });
  },

  async getAdminOpsReconciliationSnapshot(params?: PayoutAdminOpsFilters) {
    return apiRequest<PayoutAdminOpsReconciliationSnapshot>(
      `/payouts/admin-ops/reconciliation/snapshot/${buildQuery(params)}`,
      { auth: true }
    );
  },

  async exportAdminOpsRequestsCsv(params?: PayoutAdminOpsFilters) {
    return downloadCsv(`/payouts/admin-ops/requests/export.csv${buildQuery(params)}`, 'payout-requests.csv');
  },

  async exportAdminOpsLedgerCsv(params?: PayoutAdminOpsLedgerFilters) {
    return downloadCsv(`/payouts/admin-ops/ledger/export.csv${buildQuery(params)}`, 'payout-ledger.csv');
  },
};
