import { apiRequest } from '@/lib/api-client';

export type SubscriptionPlan = {
  id: string;
  code?: string;
  title?: string;
  period_days?: number;
  price?: string;
  currency?: string;
  is_active?: boolean;
};

export type SubscriptionLifecycle = {
  can_cancel: boolean;
  can_resume: boolean;
  can_sync_entitlements: boolean;
  is_terminal: boolean;
  is_access_active: boolean;
  status_label: string;
};

export type SubscriptionRenewalProjection = {
  subscription_id: string;
  status: string;
  auto_renew: boolean;
  period_days: number;
  current_period_start: string | null;
  current_period_end: string | null;
  can_renew: boolean;
  reason: string;
  next_period_start: string | null;
  next_period_end: string | null;
  amount: string;
  currency: string;
};

export type SubscriptionItem = {
  id: string;
  status?: string;
  starts_at?: string | null;
  ends_at?: string | null;
  cancelled_at?: string | null;
  auto_renew?: boolean;
  is_active?: boolean;
  remaining_days?: number | null;
  entitlement_count?: number;
  plan?: SubscriptionPlan;
  plan_name?: string;
  title?: string;
  currency?: string;
  amount?: string | number;
  price_amount?: string | number;
  started_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  current_period_start?: string | null;
  current_period_end?: string | null;
  cancel_at?: string | null;
  canceled_at?: string | null;
  lifecycle?: SubscriptionLifecycle;
  renewal_projection?: SubscriptionRenewalProjection | null;
  latest_payment?: {
    id: string;
    status?: string;
    amount?: string;
    currency?: string;
    confirmed_at?: string | null;
  } | null;
};

export type SubscriptionLifecyclePolicy = {
  supported_statuses: string[];
  access_granting_statuses: string[];
  terminal_statuses: string[];
  actions: Record<string, unknown>;
  virtual_statuses: Record<string, { persisted: boolean; reason: string }>;
};

export type SubscriptionLifecycleSummary = {
  summary: {
    total_count: number;
    trial_count: number;
    active_count: number;
    past_due_count: number;
    cancelled_count: number;
    expired_count: number;
    pending_count: number;
    auto_renew_count: number;
    due_soon_count: number;
    expired_due_count: number;
    failed_payments_count: number;
    active_entitlement_count: number;
  };
  status_breakdown: Record<string, number>;
  policy: SubscriptionLifecyclePolicy;
};

export type SubscriptionCenter = {
  summary: {
    total_count: number;
    trial_count?: number;
    active_count: number;
    cancelled_count: number;
    expired_count: number;
    past_due_count: number;
    auto_renew_count: number;
    failed_payments_count: number;
    period_spend: string;
    currency: string;
  };
  items: SubscriptionItem[];
  readiness: Array<{ code: string; label: string; done: boolean }>;
  lifecycle?: SubscriptionLifecycleSummary;
};

export type SubscriptionEntitlementSyncResult = {
  subscription_id: string;
  status: string;
  should_have_access: boolean;
  active_before: number;
  active_after: number;
  action: 'granted_or_refreshed' | 'revoked' | 'noop' | string;
};

export type SubscriptionEntitlementReconcileResult = {
  checked_count: number;
  granted_or_refreshed_count: number;
  revoked_count: number;
  noop_count: number;
  items: SubscriptionEntitlementSyncResult[];
};

export type AdminSubscriptionOverview = {
  summary: {
    total_count: number;
    trial_count?: number;
    active_count: number;
    pending_count: number;
    past_due_count: number;
    cancelled_count: number;
    expired_count: number;
    new_count: number;
    due_soon_count: number;
    expired_due_count: number;
    failed_payments_count: number;
    successful_payments_count: number;
    subscription_revenue: string;
    estimated_mrr: string;
    currency: string;
  };
  status_breakdown: Record<string, number>;
  lifecycle?: SubscriptionLifecycleSummary;
};

function reasonBody(reason = '') {
  return JSON.stringify({ reason });
}

export const subscriptionsApi = {
  getCenter: (days = 30) => apiRequest<SubscriptionCenter>(`/subscriptions/center/?days=${days}`, { auth: true }),

  getLifecyclePolicy: () => apiRequest<SubscriptionLifecyclePolicy>('/subscriptions/lifecycle-policy/', { auth: true }),

  getLifecycleSummary: (days = 30) =>
    apiRequest<SubscriptionLifecycleSummary>(`/subscriptions/lifecycle-summary/?days=${days}`, { auth: true }),

  list: () => apiRequest<SubscriptionItem[]>('/subscriptions/', { auth: true }),

  cancel: (subscriptionId: string, reason = '') =>
    apiRequest<SubscriptionItem>(`/subscriptions/${subscriptionId}/cancel/`, {
      auth: true,
      method: 'POST',
      body: reasonBody(reason),
    }),

  reactivate: (subscriptionId: string, reason = '') =>
    apiRequest<SubscriptionItem>(`/subscriptions/${subscriptionId}/reactivate/`, {
      auth: true,
      method: 'POST',
      body: reasonBody(reason),
    }),

  resume: (subscriptionId: string, reason = '') =>
    apiRequest<SubscriptionItem>(`/subscriptions/${subscriptionId}/resume/`, {
      auth: true,
      method: 'POST',
      body: reasonBody(reason),
    }),

  getRenewalProjection: (subscriptionId: string) =>
    apiRequest<SubscriptionRenewalProjection>(`/subscriptions/${subscriptionId}/renewal-projection/`, { auth: true }),

  syncEntitlements: (subscriptionId: string, reason = '') =>
    apiRequest<SubscriptionEntitlementSyncResult>(`/subscriptions/${subscriptionId}/sync-entitlements/`, {
      auth: true,
      method: 'POST',
      body: reasonBody(reason),
    }),

  getAdminOverview: (days = 30) =>
    apiRequest<AdminSubscriptionOverview>(`/subscriptions/admin/overview/?days=${days}`, { auth: true }),

  listAdminItems: (params?: { status?: string; search?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.status) qs.set('status', params.status);
    if (params?.search) qs.set('search', params.search);
    if (params?.limit) qs.set('limit', String(params.limit));
    const query = qs.toString();
    return apiRequest<SubscriptionItem[]>(`/subscriptions/admin/items/${query ? `?${query}` : ''}`, { auth: true });
  },

  getAdminLifecyclePolicy: () =>
    apiRequest<SubscriptionLifecyclePolicy>('/subscriptions/admin/lifecycle-policy/', { auth: true }),

  getAdminLifecycleSummary: (days = 30) =>
    apiRequest<SubscriptionLifecycleSummary>(`/subscriptions/admin/lifecycle-summary/?days=${days}`, { auth: true }),

  markPastDue: (subscriptionId: string, reason = '', syncEntitlements = true) =>
    apiRequest<SubscriptionItem>(`/subscriptions/${subscriptionId}/admin/mark-past-due/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify({ reason, sync_entitlements: syncEntitlements }),
    }),

  adminSyncEntitlements: (subscriptionId: string, reason = '') =>
    apiRequest<SubscriptionEntitlementSyncResult>(`/subscriptions/${subscriptionId}/admin/sync-entitlements/`, {
      auth: true,
      method: 'POST',
      body: reasonBody(reason),
    }),

  adminReconcileEntitlements: (payload?: { subscription_id?: string; limit?: number }) =>
    apiRequest<SubscriptionEntitlementReconcileResult>('/subscriptions/admin/reconcile-entitlements/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload || {}),
    }),

  expireDue: () =>
    apiRequest<{ expired_count: number; entitlement_reconciliation?: SubscriptionEntitlementReconcileResult }>(
      '/subscriptions/admin/expire-due/',
      {
        auth: true,
        method: 'POST',
        body: JSON.stringify({}),
      }
    ),
};
