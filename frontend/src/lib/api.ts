import { apiRequest, normalizeListResponse } from '@/lib/api-client';
import { accessCenterApi } from '@/modules/access-center/api';
import { authApi } from '@/modules/auth/api';
import { checkoutApi } from '@/modules/checkout/api';
import { customerHubApi } from '@/modules/customer-hub/api';
import { paymentsApi } from '@/modules/payments/api';
import { onboardingApi } from '@/modules/trainer-onboarding/api';
import { trainersApi } from '@/modules/trainers/api';
import { uploadApi } from '@/modules/upload/api';
import type {
  AdminMarketplaceHealth,
  AuditEvent,
  TrainerRiskFlag,
  ModerationOverview,
  ModerationCase,
  AnalyticsWarehouseHealth,
  AnalyticsTopTrainer,
  AnalyticsRevenuePoint,
  AnalyticsKpiOverview,
  AdminPayoutOverview,
  CheckoutResponse,
  CustomerMarketplaceHub,
  AccessCenterPayload,
  AccessDecision,
  Entitlement,
  Order,
  Payment,
  PaymentProviderSettings,
  PayoutBalance,
  PayoutRequest,
  PublicBundle,
  PublicProgram,
  PublicVideo,
  Review,
  ReviewPayload,
  Subscription,
  TrainerProfile,
  TrainerRevenueDashboard,
} from '@/types/api';

export { accessCenterApi, apiRequest, authApi, checkoutApi, customerHubApi, onboardingApi, paymentsApi, trainersApi, uploadApi };

export const publicApi = {
  async listVideos(): Promise<PublicVideo[]> {
    const payload = await apiRequest<PublicVideo[] | { results: PublicVideo[] }>('/content/videos/');
    return normalizeListResponse(payload);
  },
  getVideo: (slug: string) => apiRequest<PublicVideo>(`/content/videos/${slug}/`),

  async listPrograms(): Promise<PublicProgram[]> {
    const payload = await apiRequest<PublicProgram[] | { results: PublicProgram[] }>('/content/programs/');
    return normalizeListResponse(payload);
  },
  getProgram: (slug: string) => apiRequest<PublicProgram>(`/content/programs/${slug}/`),

  async listBundles(): Promise<PublicBundle[]> {
    const payload = await apiRequest<PublicBundle[] | { results: PublicBundle[] }>('/content/bundles/');
    return normalizeListResponse(payload);
  },
  getBundle: (slug: string) => apiRequest<PublicBundle>(`/content/bundles/${slug}/`),

  async listTrainers(): Promise<TrainerProfile[]> {
    const payload = await trainersApi.listTrainers();
    return normalizeListResponse(payload as TrainerProfile[] | { results: TrainerProfile[] });
  },
  getTrainer: trainersApi.getTrainer,

  getReviews: (targetType: string, targetId: string) =>
    apiRequest<ReviewPayload>(`/reviews/${targetType}/${targetId}/`),
};

export const privateApi = {
  getCustomerMarketplaceHub: (days = 30): Promise<CustomerMarketplaceHub> => customerHubApi.getHub(days),
  getAccessCenter: (days = 30): Promise<AccessCenterPayload> => accessCenterApi.getAccessCenter(days),
  checkAccess: (payload: { target_type: string; target_id?: string }): Promise<AccessDecision> => accessCenterApi.checkAccess(payload),
  listOrders: (): Promise<Order[]> => checkoutApi.listOrders(),
  getOrder: (orderId: string): Promise<Order> => apiRequest<Order>(`/orders/${orderId}/`, { auth: true }),
  listPayments: (): Promise<Payment[]> => paymentsApi.listPayments(),
  getPayment: (paymentId: string): Promise<Payment> => apiRequest<Payment>(`/payments/${paymentId}/`, { auth: true }),
  listSubscriptions: (): Promise<Subscription[]> => paymentsApi.listSubscriptions(),
  listEntitlements: (): Promise<Entitlement[]> => paymentsApi.listEntitlements(),
  checkoutOneTime: (payload: {
    item_type: string;
    item_id: string;
    title?: string;
    amount?: string;
    currency?: string;
    provider: string;
  }): Promise<CheckoutResponse> => checkoutApi.checkoutOneTime(payload),
  simulatePaymentSuccess: paymentsApi.simulatePaymentSuccess,
  confirmMockPayment: (paymentId: string) => apiRequest<Payment>(`/payments/${paymentId}/confirm-mock/`, { auth: true, method: 'POST' }),
  cancelMockPayment: (paymentId: string) => apiRequest<Payment>(`/payments/${paymentId}/cancel-mock/`, { auth: true, method: 'POST' }),
  providerReturn: (paymentId: string) =>
    apiRequest<{ payment_id: string; order_id: string; payment_status: string; order_status: string; redirect_path: string }>(
      `/payments/provider-return/?payment_id=${paymentId}`
    ),
  createReview: (targetType: string, targetId: string, payload: { rating: number; title: string; body: string }): Promise<Review> =>
    apiRequest<Review>(`/reviews/${targetType}/${targetId}/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  listPendingReviews: () => apiRequest<{ results: Review[] }>('/reviews/admin/pending/', { auth: true }),
  moderateReview: (reviewId: string, decision: 'publish' | 'reject') =>
    apiRequest<Review>(`/reviews/admin/${reviewId}/moderate/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify({ decision }),
    }),
  listPayouts: () => apiRequest<PayoutRequest[] | { results: PayoutRequest[] }>('/payouts/my/', { auth: true }).then(normalizeListResponse),
  getPayout: (payoutId: string) => apiRequest<PayoutRequest>(`/payouts/my/${payoutId}/`, { auth: true }),
  getPayoutBalance: () => apiRequest<PayoutBalance>('/payouts/my/balance/', { auth: true }),
  requestPayout: (payload: { amount: string; destination_masked: string }) =>
    apiRequest<PayoutRequest>('/payouts/my/request/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  getAdminPayoutOverview: () => apiRequest<AdminPayoutOverview>('/payouts/admin/overview/', { auth: true }),
  listAdminPayouts: (statusValue?: string) =>
    apiRequest<PayoutRequest[] | { results: PayoutRequest[] }>(`/payouts/admin/${statusValue ? `?status=${encodeURIComponent(statusValue)}` : ''}`, { auth: true }).then(normalizeListResponse),
  getAdminPayout: (payoutId: string) => apiRequest<PayoutRequest>(`/payouts/admin/${payoutId}/`, { auth: true }),
  transitionAdminPayout: (payoutId: string, payload: { action: 'approve' | 'processing' | 'paid' | 'reject'; reason?: string; external_reference?: string }) =>
    apiRequest<PayoutRequest>(`/payouts/admin/${payoutId}/transition/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    }),
getAdminAnalyticsOverview: (days = 30) => apiRequest<AnalyticsKpiOverview>(`/analytics/overview/?days=${days}`, { auth: true }),
getAdminAnalyticsRevenueSeries: (days = 30) => apiRequest<AnalyticsRevenuePoint[]>(`/analytics/revenue-timeseries/?days=${days}`, { auth: true }),
getAdminAnalyticsTopTrainers: (days = 30, limit = 10) => apiRequest<AnalyticsTopTrainer[]>(`/analytics/top-trainers/?days=${days}&limit=${limit}`, { auth: true }),
getAdminAnalyticsWarehouseHealth: () => apiRequest<AnalyticsWarehouseHealth>('/analytics/warehouse-health/', { auth: true }),
getAdminModerationOverview: () => apiRequest<ModerationOverview>('/moderation/admin/overview/', { auth: true }),
getAdminMarketplaceMaintenance: () =>
  apiRequest<Record<string, unknown>>('/moderation/admin/maintenance/', { auth: true }),
runAdminMarketplaceMaintenance: (dryRun = false) =>
  apiRequest<Record<string, unknown>>('/moderation/admin/maintenance/', {
    auth: true,
    method: 'POST',
    body: JSON.stringify({ dry_run: dryRun }),
  }),
listAdminModerationCases: (params?: { status?: string; queue?: string; search?: string }) => {
  const search = new URLSearchParams();
  if (params?.status) search.set('status', params.status);
  if (params?.queue) search.set('queue', params.queue);
  if (params?.search) search.set('search', params.search);
  const query = search.toString();
  return apiRequest<ModerationCase[] | { results: ModerationCase[] }>(`/moderation/admin/queue/${query ? `?${query}` : ''}`, { auth: true }).then(normalizeListResponse);
},
getAdminModerationCase: (caseId: string) => apiRequest<ModerationCase>(`/moderation/admin/cases/${caseId}/`, { auth: true }),
assignAdminModerationCase: (caseId: string, assigneeId?: string) =>
  apiRequest<ModerationCase>(`/moderation/admin/cases/${caseId}/assign/`, {
    auth: true,
    method: 'POST',
    body: JSON.stringify({ assignee_id: assigneeId || null }),
  }),
decideAdminModerationCase: (caseId: string, payload: { decision: 'approved' | 'rejected' | 'needs_changes' | 'escalated'; reason?: string; metadata?: Record<string, unknown> }) =>
  apiRequest<ModerationCase>(`/moderation/admin/cases/${caseId}/decision/`, {
    auth: true,
    method: 'POST',
    body: JSON.stringify(payload),
  }),
listAdminRiskFlags: (activeOnly = true) =>
  apiRequest<TrainerRiskFlag[] | { results: TrainerRiskFlag[] }>(`/moderation/admin/risk-flags/${activeOnly ? '?active=true' : ''}`, { auth: true }).then(normalizeListResponse),
createAdminRiskFlag: (payload: { trainer_id: string; code: string; label: string; risk_level: 'low' | 'medium' | 'high' | 'critical'; details?: Record<string, unknown> }) =>
  apiRequest<TrainerRiskFlag>('/moderation/admin/risk-flags/create/', {
    auth: true,
    method: 'POST',
    body: JSON.stringify(payload),
  }),
resolveAdminRiskFlag: (flagId: string) => apiRequest<TrainerRiskFlag>(`/moderation/admin/risk-flags/${flagId}/resolve/`, { auth: true, method: 'POST' }),
  getAdminMarketplaceHealth: (days = 30) => apiRequest<AdminMarketplaceHealth>(`/admin/marketplace-health/?days=${days}`, { auth: true }),
  listAdminAuditEvents: () => apiRequest<AuditEvent[] | { results: AuditEvent[] }>(`/audit/admin/events/`, { auth: true }).then(normalizeListResponse),
  getPaymentProviderSettings: () => apiRequest<PaymentProviderSettings>('/platform-settings/payment-providers/', { auth: true }),
  updatePaymentProviderSettings: (payload: PaymentProviderSettings) =>
    apiRequest<PaymentProviderSettings>('/platform-settings/payment-providers/', {
      auth: true,
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  getTrainerRevenueDashboard: () => apiRequest<TrainerRevenueDashboard>('/analytics/trainer-dashboard/', { auth: true }),
};
