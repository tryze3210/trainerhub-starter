import { apiRequest } from '@/lib/api-client';

export type ReconciliationStatus = 'ok' | 'degraded' | 'critical' | string;
export type ReconciliationSeverity = 'info' | 'warning' | 'critical' | string;

export type ReconciliationRelatedEntity = {
  entity_type: string;
  entity_id: string;
  label?: string;
  href?: string;
};

export type ReconciliationIssue = {
  code: string;
  severity: ReconciliationSeverity;
  entity_type: string;
  entity_id: string;
  message: string;
  suggested_action: string;
  related?: ReconciliationRelatedEntity[];
  evidence?: Record<string, unknown>;
};

export type ReconciliationCheck = {
  code: string;
  description?: string;
};

export type ReconciliationSection = {
  status: ReconciliationStatus;
  metrics?: Record<string, unknown>;
  checks?: ReconciliationCheck[];
  issue_count: number;
  issues: ReconciliationIssue[];
};

export type AdminReconciliationReport = {
  status: ReconciliationStatus;
  generated_at: string;
  summary: {
    total_issues: number;
    critical_count: number;
    warning_count: number;
    info_count?: number;
    by_severity?: Record<string, number>;
    [key: string]: unknown;
  };
  sections: Record<string, ReconciliationSection | undefined>;
};



export type ReconciliationRepairAction =
  | 'retry_outbox'
  | 'mark_outbox_dead'
  | 'reprocess_webhook'
  | 'grant_order_access'
  | 'revoke_entitlement'
  | 'project_payout_accrual'
  | 'reverse_payout_accrual';

export type ReconciliationRepairRequest = {
  action: ReconciliationRepairAction;
  entity_type: 'outbox_message' | 'payment_webhook' | 'payment' | 'order' | 'entitlement' | 'payout_ledger' | string;
  entity_id: string;
  reason: string;
  force?: boolean;
};

export type ReconciliationRepairResult = {
  action: string;
  status: string;
  entity_type: string;
  entity_id: string;
  message: string;
  changed: boolean;
  result: Record<string, unknown>;
  audit_event_id?: string;
  audit_event_href?: string;
  entity_href?: string;
  reconciliation_href?: string;
  audit?: {
    event_id?: string;
    event_type?: string;
    entity_type?: string;
    entity_id?: string;
    created_at?: string | null;
    [key: string]: unknown;
  };
};

export type ReconciliationFilters = {
  limit?: number;
};

function buildQuery(params?: ReconciliationFilters) {
  const query = new URLSearchParams();
  if (params?.limit) query.set('limit', String(params.limit));
  const value = query.toString();
  return value ? `?${value}` : '';
}

export const adminReconciliationApi = {
  getReport: (params?: ReconciliationFilters) =>
    apiRequest<AdminReconciliationReport>(`/ops/admin/reconciliation-report/${buildQuery(params)}`, {
      auth: true,
    }),

  runRepair: (payload: ReconciliationRepairRequest) =>
    apiRequest<ReconciliationRepairResult>('/ops/admin/reconciliation-repair/', {
      method: 'POST',
      auth: true,
      body: JSON.stringify(payload),
    }),
};
