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
  latest_payment?: {
    id: string;
    status?: string;
    amount?: string;
    currency?: string;
    confirmed_at?: string | null;
  } | null;
};

export type SubscriptionCenter = {
  summary: {
    total_count: number;
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
};

export type AdminSubscriptionOverview = {
  summary: {
    total_count: number;
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
};

export const subscriptionsApi = {
  getCenter: (days = 30) =>
    apiRequest<SubscriptionCenter>(`/subscriptions/center/?days=${days}`, { auth: true }),

  list: () => apiRequest<SubscriptionItem[]>(`/subscriptions/`, { auth: true }),

  cancel: (subscriptionId: string, reason = '') =>
    apiRequest<SubscriptionItem>(`/subscriptions/${subscriptionId}/cancel/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),

  reactivate: (subscriptionId: string) =>
    apiRequest<SubscriptionItem>(`/subscriptions/${subscriptionId}/reactivate/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify({}),
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

  markPastDue: (subscriptionId: string, reason = '') =>
    apiRequest<SubscriptionItem>(`/subscriptions/${subscriptionId}/admin/mark-past-due/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),

  expireDue: () =>
    apiRequest<{ expired_count: number }>(`/subscriptions/admin/expire-due/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify({}),
    }),
};
