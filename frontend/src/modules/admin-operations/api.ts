import { apiRequest } from '@/lib/api-client';

export type JsonRecord = Record<string, unknown>;
export type OperationsStatus = 'ok' | 'degraded' | 'critical' | 'missing' | 'unavailable' | string;

export type OperationsIssue = {
  code: string;
  severity: 'warning' | 'critical' | 'info' | string;
  count?: number;
  amount?: string;
};

export type OperationsBucket = {
  key?: string;
  status?: string;
  count: number;
  amount?: string;
};

export type OperationsRecentOutboxMessage = {
  id: string;
  status: string;
  topic?: string;
  attempts?: number;
  event_type?: string;
  aggregate_type?: string;
  aggregate_id?: string;
  last_error?: string;
  updated_at?: string | null;
};

export type OperationsRecentWebhookEvent = {
  id: string;
  provider?: string;
  event_type?: string;
  external_event_id?: string;
  payment_id?: string;
  status?: string;
  error_message?: string;
  received_at?: string | null;
  processed_at?: string | null;
};

export type OperationsRecentRiskPayment = {
  id: string;
  status: string;
  amount?: string;
  currency?: string;
  provider?: string;
  external_payment_id?: string;
  order_id?: string;
  updated_at?: string | null;
};

export type OperationsRecentLedgerEntry = {
  id: string;
  entry_type?: string;
  direction?: string;
  amount?: string;
  currency?: string;
  source_type?: string;
  source_id?: string;
  trainer_id?: string;
  created_at?: string | null;
};

export type OperationsRecentModerationCase = {
  id: string;
  status?: string;
  priority?: number;
  target_type?: string;
  target_id?: string;
  title?: string;
  trainer_id?: string;
  updated_at?: string | null;
};

export type OperationsSection = {
  status: OperationsStatus;
  issues?: OperationsIssue[];
  counts?: JsonRecord;
  amounts?: JsonRecord;
  risk_amounts?: JsonRecord;
  by_status?: OperationsBucket[];
  payout_request_by_status?: OperationsBucket[];
  case_by_status?: OperationsBucket[];
  flag_by_level?: OperationsBucket[];
  recent_problem_messages?: OperationsRecentOutboxMessage[];
  recent_problem_events?: OperationsRecentWebhookEvent[];
  recent_risk_payments?: OperationsRecentRiskPayment[];
  recent_risk_ledger_entries?: OperationsRecentLedgerEntry[];
  recent_payment_risk_cases?: OperationsRecentModerationCase[];
  [key: string]: unknown;
};

export type AdminOperationsDashboard = {
  status: OperationsStatus;
  generated_at: string;
  sections: {
    outbox?: OperationsSection;
    webhooks?: OperationsSection;
    payments?: OperationsSection;
    payouts?: OperationsSection;
    moderation?: OperationsSection;
    [key: string]: OperationsSection | undefined;
  };
  summary: {
    critical_count?: number;
    warning_count?: number;
    critical_items?: OperationsIssue[];
    warning_items?: OperationsIssue[];
    [key: string]: unknown;
  };
};

export type OperationsHubAction = {
  key: string;
  title: string;
  method: string;
  api_href: string;
  risk: 'low' | 'medium' | 'high' | 'critical' | string;
  description?: string;
};

export type OperationsHubNavigationItem = {
  key: string;
  title: string;
  href: string;
  api_href?: string;
  description?: string;
};

export type OperationsHubPayload = {
  status: OperationsStatus;
  generated_at: string;
  filters?: JsonRecord;
  summary: {
    status?: OperationsStatus;
    operations_critical_count?: number;
    operations_warning_count?: number;
    reconciliation_total_issues?: number;
    reconciliation_critical_count?: number;
    reconciliation_repairable_issues?: number;
    reconciliation_alert_count?: number;
    scheduled_snapshot_due?: boolean;
    latest_reconciliation_snapshot_id?: string | null;
    latest_reconciliation_status?: OperationsStatus;
    latest_reconciliation_direction?: string;
    [key: string]: unknown;
  };
  sections: {
    async_infra?: {
      status: OperationsStatus;
      outbox?: OperationsSection;
      webhooks?: OperationsSection;
      [key: string]: unknown;
    };
    money_risk?: {
      status: OperationsStatus;
      payments?: OperationsSection;
      payouts?: OperationsSection;
      moderation?: OperationsSection;
      [key: string]: unknown;
    };
    reconciliation?: {
      status: OperationsStatus;
      metrics?: JsonRecord;
      schedule?: JsonRecord;
      alerts?: JsonRecord;
      issue_registry?: {
        status?: OperationsStatus;
        summary?: JsonRecord;
        issues?: Array<JsonRecord>;
        [key: string]: unknown;
      };
      [key: string]: unknown;
    };
    [key: string]: unknown;
  };
  raw_operations_dashboard?: AdminOperationsDashboard;
  quick_actions: OperationsHubAction[];
  navigation: OperationsHubNavigationItem[];
};


export type OperationsReadinessCheck = {
  key: string;
  category: string;
  title: string;
  status: OperationsStatus;
  detail?: string;
  version?: string;
  description?: string;
  expected_path?: string;
  actual_path?: string;
  [key: string]: unknown;
};

export type OperationsReadinessPayload = {
  status: OperationsStatus;
  generated_at: string;
  version: string;
  scope: string;
  summary: {
    total_checks?: number;
    ok_count?: number;
    warning_count?: number;
    degraded_count?: number;
    critical_count?: number;
    by_status?: JsonRecord;
    by_category?: JsonRecord;
    [key: string]: unknown;
  };
  checks: OperationsReadinessCheck[];
  api_surface: Array<JsonRecord>;
  frontend_surface: Array<JsonRecord>;
  environment_flags: Array<JsonRecord>;
  smoke_commands?: Array<JsonRecord>;
  management_commands?: Array<JsonRecord>;
  recommendations?: Array<JsonRecord>;
};


export type CommerceReadinessPayload = {
  status: OperationsStatus;
  generated_at: string;
  version: string;
  scope: string;
  summary: {
    total_checks?: number;
    ok_count?: number;
    warning_count?: number;
    degraded_count?: number;
    critical_count?: number;
    by_status?: JsonRecord;
    by_category?: JsonRecord;
    [key: string]: unknown;
  };
  checks: OperationsReadinessCheck[];
  api_surface: Array<JsonRecord>;
  frontend_surface?: Array<JsonRecord>;
  smoke_commands?: Array<JsonRecord>;
  management_commands?: Array<JsonRecord>;
  recommendations?: Array<JsonRecord>;
};

export type OutboxActionResult = {
  id?: string;
  status?: string;
  attempts?: number;
  processed_at?: string | null;
  last_error?: string;
  [key: string]: unknown;
};

export type DispatchOutboxResult = {
  claimed?: number;
  processed?: number;
  failed?: number;
  skipped?: number;
  dead?: number;
  [key: string]: unknown;
};

export type RequeueStuckOutboxResult = {
  requeued?: number;
  matched?: number;
  [key: string]: unknown;
};

export type ReleaseRiskHoldResult = {
  status?: string;
  payment_id?: string;
  released_amount?: string;
  reason?: string;
  [key: string]: unknown;
};

function query(params: Record<string, unknown>) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return;
    search.set(key, String(value));
  });
  const rendered = search.toString();
  return rendered ? `?${rendered}` : '';
}

export const adminOperationsApi = {
  getDashboard: () =>
    apiRequest<AdminOperationsDashboard>('/ops/admin/operations-dashboard/', {
      auth: true,
    }),

  getHub: (params: { snapshot_limit?: number; issue_limit?: number; source?: string; include_issues?: boolean; include_alerts?: boolean } = {}) =>
    apiRequest<OperationsHubPayload>(
      `/ops/admin/operations-hub/${query({
        snapshot_limit: params.snapshot_limit ?? 30,
        issue_limit: params.issue_limit ?? 20,
        source: params.source ?? '',
        include_issues: params.include_issues ?? true,
        include_alerts: params.include_alerts ?? true,
      })}`,
      { auth: true }
    ),

  getReadiness: (params: { include_commands?: boolean; include_recommendations?: boolean } = {}) =>
    apiRequest<OperationsReadinessPayload>(
      `/ops/admin/operations-readiness/${query({
        include_commands: params.include_commands ?? true,
        include_recommendations: params.include_recommendations ?? true,
      })}`,
      { auth: true }
    ),



  getCommerceReadiness: (params: { include_commands?: boolean; include_frontend?: boolean; include_recommendations?: boolean } = {}) =>
    apiRequest<CommerceReadinessPayload>(
      `/ops/admin/commerce-readiness/${query({
        include_commands: params.include_commands ?? true,
        include_frontend: params.include_frontend ?? true,
        include_recommendations: params.include_recommendations ?? true,
      })}`,
      { auth: true }
    ),

  dispatchOutbox: (batchSize = 100) =>
    apiRequest<DispatchOutboxResult>('/events/outbox/dispatch/', {
      method: 'POST',
      auth: true,
      body: JSON.stringify({ batch_size: batchSize }),
    }),

  requeueStuckOutbox: (payload: { older_than_minutes?: number; limit?: number } = {}) =>
    apiRequest<RequeueStuckOutboxResult>('/events/outbox/requeue-stuck/', {
      method: 'POST',
      auth: true,
      body: JSON.stringify({
        older_than_minutes: payload.older_than_minutes ?? 15,
        limit: payload.limit ?? 100,
      }),
    }),

  retryOutboxMessage: (messageId: string, payload: { force?: boolean; reset_attempts?: boolean } = {}) =>
    apiRequest<OutboxActionResult>(`/events/outbox/${messageId}/retry/`, {
      method: 'POST',
      auth: true,
      body: JSON.stringify({
        force: payload.force ?? true,
        reset_attempts: payload.reset_attempts ?? true,
      }),
    }),

  markOutboxDead: (messageId: string, reason: string) =>
    apiRequest<OutboxActionResult>(`/events/outbox/${messageId}/dead/`, {
      method: 'POST',
      auth: true,
      body: JSON.stringify({ reason }),
    }),

  releaseRiskHold: (paymentId: string, reason = 'manual_ops_release_from_admin_operations') =>
    apiRequest<ReleaseRiskHoldResult>('/payouts/admin/risk-holds/release/', {
      method: 'POST',
      auth: true,
      body: JSON.stringify({ payment_id: paymentId, reason }),
    }),

  captureReconciliationSnapshot: (payload: { limit?: number; source?: string; correlation_id?: string } = {}) =>
    apiRequest<JsonRecord>('/ops/admin/reconciliation-snapshots/capture/', {
      method: 'POST',
      auth: true,
      body: JSON.stringify({
        limit: payload.limit ?? 100,
        source: payload.source ?? 'manual',
        correlation_id: payload.correlation_id ?? `operations-hub-${Date.now()}`,
      }),
    }),

  evaluateReconciliationAlerts: () =>
    apiRequest<JsonRecord>('/ops/admin/reconciliation-snapshots/alerts/', {
      auth: true,
    }),
};
