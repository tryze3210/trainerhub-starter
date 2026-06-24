import { apiRequest, normalizeListResponse, type PaginatedResponse } from '@/lib/api-client';

export type SubscriptionStatus = 'trial' | 'pending' | 'active' | 'past_due' | 'cancelled' | 'expired' | string;

export type AdminSubscriptionPlan = {
  id?: string;
  code?: string;
  title?: string;
  period_days?: number;
  price?: string | number;
  currency?: string;
  is_active?: boolean;
};

export type AdminSubscriptionItem = {
  id: string;
  status?: SubscriptionStatus;
  user_id?: string;
  customer_id?: string;
  trainer_id?: string | null;
  plan?: AdminSubscriptionPlan | null;
  plan_name?: string;
  title?: string;
  currency?: string;
  amount?: string | number;
  price_amount?: string | number;
  starts_at?: string | null;
  ends_at?: string | null;
  started_at?: string | null;
  current_period_start?: string | null;
  current_period_end?: string | null;
  cancelled_at?: string | null;
  cancel_at?: string | null;
  canceled_at?: string | null;
  auto_renew?: boolean;
  is_active?: boolean;
  remaining_days?: number | null;
  entitlement_count?: number;
  latest_payment?: {
    id?: string;
    status?: string;
    amount?: string | number;
    currency?: string;
    confirmed_at?: string | null;
  } | null;
  created_at?: string | null;
  updated_at?: string | null;
  metadata?: Record<string, unknown>;
};

export type AdminSubscriptionOverview = {
  summary?: {
    total_count?: number;
    trial_count?: number;
    active_count?: number;
    pending_count?: number;
    past_due_count?: number;
    cancelled_count?: number;
    expired_count?: number;
    new_count?: number;
    due_soon_count?: number;
    expired_due_count?: number;
    failed_payments_count?: number;
    successful_payments_count?: number;
    subscription_revenue?: string | number;
    estimated_mrr?: string | number;
    currency?: string;
    [key: string]: unknown;
  };
  status_breakdown?: Record<string, number> | Array<{ status: string; count: number }>;
  [key: string]: unknown;
};

export type SubscriptionLifecyclePolicy = {
  statuses?: Array<{
    code: string;
    label?: string;
    persisted?: boolean;
    terminal?: boolean;
    can_cancel?: boolean;
    can_resume?: boolean;
    can_mark_past_due?: boolean;
    can_sync_entitlements?: boolean;
    description?: string;
  }>;
  transitions?: Record<string, string[]> | Array<{ from: string; to: string[] }>;
  [key: string]: unknown;
};

export type SubscriptionLifecycleSummary = {
  generated_at?: string;
  status?: string;
  summary?: Record<string, unknown>;
  buckets?: Array<{ status: string; count: number }>;
  issues?: Array<{ code: string; severity?: string; count?: number; message?: string }>;
  [key: string]: unknown;
};

export type SubscriptionRenewalProjection = {
  subscription_id?: string;
  current_status?: string;
  next_renewal_at?: string | null;
  period_days?: number | null;
  amount?: string | number | null;
  currency?: string;
  auto_renew?: boolean;
  will_renew?: boolean;
  reasons?: string[];
  [key: string]: unknown;
};

export type SubscriptionActionResult = {
  id?: string;
  status?: string;
  detail?: string;
  expired_count?: number;
  synced_count?: number;
  repaired_count?: number;
  dry_run?: boolean;
  [key: string]: unknown;
};

export type SubscriptionListParams = {
  status?: string;
  search?: string;
  limit?: number;
};

function qs(params: Record<string, string | number | boolean | undefined | null>): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, String(value));
    }
  });
  const query = search.toString();
  return query ? `?${query}` : '';
}

export const adminSubscriptionsApi = {
  getOverview(days = 30): Promise<AdminSubscriptionOverview> {
    return apiRequest<AdminSubscriptionOverview>(`/subscriptions/admin/overview/${qs({ days })}`, { auth: true });
  },

  async listItems(params: SubscriptionListParams = {}): Promise<AdminSubscriptionItem[]> {
    const payload = await apiRequest<AdminSubscriptionItem[] | PaginatedResponse<AdminSubscriptionItem>>(
      `/subscriptions/admin/items/${qs(params)}`,
      { auth: true },
    );
    return normalizeListResponse<AdminSubscriptionItem>(payload);
  },

  getItem(subscriptionId: string): Promise<AdminSubscriptionItem> {
    return apiRequest<AdminSubscriptionItem>(`/subscriptions/${subscriptionId}/`, { auth: true });
  },

  getLifecyclePolicy(): Promise<SubscriptionLifecyclePolicy> {
    return apiRequest<SubscriptionLifecyclePolicy>('/subscriptions/admin/lifecycle-policy/', { auth: true });
  },

  getLifecycleSummary(days = 30): Promise<SubscriptionLifecycleSummary> {
    return apiRequest<SubscriptionLifecycleSummary>(`/subscriptions/admin/lifecycle-summary/${qs({ days })}`, { auth: true });
  },

  getRenewalProjection(subscriptionId: string): Promise<SubscriptionRenewalProjection> {
    return apiRequest<SubscriptionRenewalProjection>(`/subscriptions/${subscriptionId}/renewal-projection/`, { auth: true });
  },

  markPastDue(subscriptionId: string, reason: string): Promise<SubscriptionActionResult> {
    return apiRequest<SubscriptionActionResult>(`/subscriptions/${subscriptionId}/admin/mark-past-due/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  },

  syncEntitlements(subscriptionId: string, reason = 'admin_subscription_ops_sync'): Promise<SubscriptionActionResult> {
    return apiRequest<SubscriptionActionResult>(`/subscriptions/${subscriptionId}/admin/sync-entitlements/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  },

  expireDue(reason = 'admin_subscription_ops_expire_due'): Promise<SubscriptionActionResult> {
    return apiRequest<SubscriptionActionResult>('/subscriptions/admin/expire-due/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  },

  reconcileEntitlements(dryRun = true): Promise<SubscriptionActionResult> {
    return apiRequest<SubscriptionActionResult>('/subscriptions/admin/reconcile-entitlements/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify({ dry_run: dryRun }),
    });
  },
};
