import { apiRequest } from '@/lib/api-client';

export type OperationsStatus = 'ok' | 'degraded' | 'critical' | string;

export type OperationsIssue = {
  code: string;
  severity: 'warning' | 'critical' | string;
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
  issues: OperationsIssue[];
  counts?: Record<string, string | number | null | undefined>;
  amounts?: Record<string, string | number | null | undefined>;
  risk_amounts?: Record<string, string | number | null | undefined>;
  by_status?: OperationsBucket[];
  payout_request_by_status?: OperationsBucket[];
  case_by_status?: OperationsBucket[];
  flag_by_level?: OperationsBucket[];
  recent_problem_messages?: OperationsRecentOutboxMessage[];
  recent_problem_events?: OperationsRecentWebhookEvent[];
  recent_risk_payments?: OperationsRecentRiskPayment[];
  recent_risk_ledger_entries?: OperationsRecentLedgerEntry[];
  recent_payment_risk_cases?: OperationsRecentModerationCase[];
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

export const adminOperationsApi = {
  getDashboard: () =>
    apiRequest<AdminOperationsDashboard>('/ops/admin/operations-dashboard/', {
      auth: true,
    }),

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
};
